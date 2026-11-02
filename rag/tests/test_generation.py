"""Exercise the real OpenAI SDK with a local mock transport; never call the API."""

import asyncio
import json

import httpx
import openai
import pytest

from rag.generation import DraftError, DraftSettings, generate_answer


PASSAGES = [{"title": "Fixture", "section": "Demo", "text": "Test passage.",
             "source_sha256": "local-provenance-not-for-provider"}]


def install_transport(monkeypatch, handler):
    real_client = openai.AsyncOpenAI
    options = []

    def factory(**kwargs):
        options.append(kwargs.copy())
        return real_client(**kwargs, http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)))

    monkeypatch.setattr("rag.generation.openai.AsyncOpenAI", factory)
    return options


def response_body(text="Fixture answer [S1].", status="completed"):
    return {"id": "resp_fixture", "object": "response", "created_at": 1,
            "status": status, "model": "gpt-5.4-mini",
            "output": [{"id": "msg_fixture", "type": "message", "role": "assistant",
                        "status": "completed", "content": [
                            {"type": "output_text", "text": text, "annotations": []}]}]}


def test_responses_request_uses_only_retrieved_context_and_bounded_settings(monkeypatch):
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json=response_body())

    monkeypatch.setenv("OPENAI_BASE_URL", "https://unrelated.invalid")
    options = install_transport(monkeypatch, handler)
    answer = asyncio.run(generate_answer("Question?", PASSAGES, DraftSettings("fake-key")))
    assert answer == "Fixture answer [S1]."
    assert len(requests) == 1
    assert requests[0].url == "https://api.openai.com/v1/responses"
    payload = json.loads(requests[0].content)
    assert payload["store"] is False
    assert payload["model"] == "gpt-5.4-mini"
    assert payload["max_output_tokens"] == 1600
    assert payload["reasoning"] == {"effort": "none"}
    assert "tools" not in payload
    context = json.loads(payload["input"])
    assert context["question"] == "Question?"
    assert context["passages"][0]["citation"] == "S1"
    assert "source_sha256" not in context["passages"][0]
    assert options[0]["max_retries"] == 0
    assert options[0]["timeout"] == 35
    assert "fake-key" not in repr(DraftSettings("fake-key"))


@pytest.mark.parametrize("status,provider_code,expected", [
    (400, "invalid_parameter", "openai_bad_request"),
    (401, "invalid_api_key", "openai_auth"),
    (403, "permission_denied", "openai_permission"),
    (404, "model_not_found", "openai_model_unavailable"),
    (429, "insufficient_quota", "openai_quota"),
    (429, "rate_limit_exceeded", "openai_rate_limit"),
    (500, "server_error", "openai_unavailable"),
])
def test_provider_errors_are_specific_redacted_and_not_retried(monkeypatch, status, provider_code, expected):
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(status, json={"error": {"code": provider_code,
                              "message": "sensitive-provider-detail", "type": "test_error"}})

    install_transport(monkeypatch, handler)
    with pytest.raises(DraftError) as caught:
        asyncio.run(generate_answer("Question?", PASSAGES, DraftSettings("fake-key")))
    assert caught.value.code == expected
    assert "sensitive-provider-detail" not in str(caught.value)
    assert "fake-key" not in str(caught.value)
    assert len(requests) == 1


@pytest.mark.parametrize("exc_type,code", [(httpx.ConnectError, "openai_connection"),
                                         (httpx.ReadTimeout, "openai_timeout")])
def test_transport_failure_is_actionable(monkeypatch, exc_type, code):
    def handler(request):
        raise exc_type("transport-error", request=request)

    install_transport(monkeypatch, handler)
    with pytest.raises(DraftError) as caught:
        asyncio.run(generate_answer("Question?", PASSAGES, DraftSettings("fake-key")))
    assert caught.value.code == code


def test_wall_clock_deadline_cancels_a_stalled_provider(monkeypatch):
    async def handler(request):
        await asyncio.sleep(2)
        return httpx.Response(200, json=response_body())

    install_transport(monkeypatch, handler)
    with pytest.raises(DraftError) as caught:
        asyncio.run(generate_answer("Question?", PASSAGES, DraftSettings("fake-key", timeout_seconds=.01)))
    assert caught.value.code == "openai_timeout"


@pytest.mark.parametrize("text,status,code", [("", "completed", "openai_empty"),
                                             ("Partial", "incomplete", "openai_incomplete")])
def test_empty_or_partial_draft_is_not_presented_as_complete(monkeypatch, text, status, code):
    install_transport(monkeypatch, lambda request: httpx.Response(200, json=response_body(text, status)))
    with pytest.raises(DraftError) as caught:
        asyncio.run(generate_answer("Question?", PASSAGES, DraftSettings("fake-key")))
    assert caught.value.code == code


@pytest.mark.parametrize("name,value", [("OPENAI_TIMEOUT_SECONDS", "nan"),
                                        ("OPENAI_TIMEOUT_SECONDS", "120"),
                                        ("OPENAI_MAX_OUTPUT_TOKENS", "wrong"),
                                        ("OPENAI_REASONING_EFFORT", "invalid")])
def test_bad_settings_fail_before_sending_requests(monkeypatch, name, value):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "fake-key")
    monkeypatch.setenv(name, value)
    with pytest.raises(DraftError) as caught:
        DraftSettings.from_env()
    assert caught.value.code == "openai_config_invalid"


def test_groq_uses_selected_key_endpoint_and_supported_payload(monkeypatch):
    requests = []

    def handler(request):
        requests.append(request)
        body = response_body()
        body["model"] = "openai/gpt-oss-20b"
        body["output"].insert(0, {"id": "rs_fixture", "type": "reasoning", "summary": []})
        return httpx.Response(200, json=body)

    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "groq-test-secret")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-test-secret")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://unrelated.invalid")
    monkeypatch.setenv("GROQ_BASE_URL", "https://unrelated.invalid")
    for suffix in ["MODEL", "REASONING_EFFORT", "TIMEOUT_SECONDS", "MAX_OUTPUT_TOKENS"]:
        monkeypatch.delenv(f"GROQ_{suffix}", raising=False)
    options = install_transport(monkeypatch, handler)
    settings = DraftSettings.from_env()
    answer = asyncio.run(generate_answer("Question?", PASSAGES, settings))
    assert settings.api_key == "groq-test-secret"
    assert settings.model == "openai/gpt-oss-20b"
    assert answer == "Fixture answer [S1]."
    assert requests[0].url == "https://api.groq.com/openai/v1/responses"
    assert requests[0].headers["authorization"] == "Bearer groq-test-secret"
    payload = json.loads(requests[0].content)
    assert payload["reasoning"] == {"effort": "low"}
    assert payload["max_output_tokens"] == 2400
    assert "store" not in payload
    assert "tools" not in payload
    assert options[0]["max_retries"] == 0


@pytest.mark.parametrize("status,provider_code,expected", [
    (401, "invalid_api_key", "groq_auth"),
    (404, "model_not_found", "groq_model_unavailable"),
    (429, "rate_limit_exceeded", "groq_rate_limit"),
    (429, "insufficient_quota", "groq_quota"),
    (413, "request_too_large", "groq_request_too_large"),
    (500, "server_error", "groq_unavailable"),
])
def test_groq_errors_are_specific_without_provider_fallback(monkeypatch, status, provider_code, expected):
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(status, json={"error": {"code": provider_code,
                              "message": "sensitive-test-detail", "type": "test_error"}})

    install_transport(monkeypatch, handler)
    settings = DraftSettings("fake-groq-key", model="openai/gpt-oss-20b", reasoning_effort="low", provider="groq")
    with pytest.raises(DraftError) as caught:
        asyncio.run(generate_answer("Question?", PASSAGES, settings))
    assert caught.value.code == expected
    assert "sensitive-test-detail" not in str(caught.value)
    assert "OpenAI Platform" not in str(caught.value)
    assert len(requests) == 1
    assert requests[0].url.host == "api.groq.com"


def test_unknown_provider_is_rejected_before_requests(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "unrelated")
    with pytest.raises(DraftError) as caught:
        DraftSettings.from_env()
    assert caught.value.code == "provider_invalid"


def test_groq_gpt_oss_rejects_unsupported_none_reasoning(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setenv("GROQ_MODEL", "openai/gpt-oss-20b")
    monkeypatch.setenv("GROQ_REASONING_EFFORT", "none")
    with pytest.raises(DraftError) as caught:
        DraftSettings.from_env()
    assert caught.value.code == "groq_config_invalid"
