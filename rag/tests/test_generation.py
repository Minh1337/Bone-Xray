"""Exercise OpenRouter routing with local mocked HTTP only; never call a provider."""

import asyncio
import json

import httpx
import openai
import pytest

from rag.generation import DraftError, DraftSettings, generate_answer, generate_image_answer


PASSAGES = [{"title": "Fixture", "section": "Demo", "text": "Test passage.",
             "source_sha256": "local-provenance-not-for-provider"}]
PAID_MODEL = "qwen/qwen3.5-flash-02-23"
VISION_MODEL = "google/gemma-4-31b-it:free"


def install_transport(monkeypatch, handler):
    real_client = openai.AsyncOpenAI
    options = []

    def factory(**kwargs):
        options.append(kwargs.copy())
        return real_client(**kwargs, http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)))

    monkeypatch.setattr("rag.generation.openai.AsyncOpenAI", factory)
    return options


def completion(text="Fixture answer [S1].", finish_reason="stop", *, tool_calls=None):
    return {"id": "chatcmpl_fixture", "object": "chat.completion", "created": 1,
            "model": "openrouter/free", "choices": [{"index": 0, "finish_reason": finish_reason,
            "message": {"role": "assistant", "content": text, "tool_calls": tool_calls}}]}


def settings():
    return DraftSettings("fake-key")


def test_openrouter_chat_request_uses_only_retrieved_context_and_bounded_settings(monkeypatch):
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json=completion())

    monkeypatch.setenv("OPENAI_BASE_URL", "https://unrelated.invalid")
    options = install_transport(monkeypatch, handler)
    answer = asyncio.run(generate_answer("Question?", PASSAGES, settings()))
    assert answer == "Fixture answer [S1]."
    assert answer.provider == "openrouter" and answer.model == "openrouter/free"
    assert len(requests) == 1
    assert requests[0].url == "https://openrouter.ai/api/v1/chat/completions"
    payload = json.loads(requests[0].content)
    assert payload["model"] == "openrouter/free"
    assert payload["max_tokens"] == 1600
    assert payload["messages"][0]["role"] == "system"
    context = json.loads(payload["messages"][1]["content"])
    assert context["question"] == "Question?"
    assert context["passages"][0]["citation"] == "S1"
    assert "source_sha256" not in context["passages"][0]
    assert options[0]["max_retries"] == 0
    assert options[0]["timeout"] == 15.0
    assert "fake-key" not in repr(settings())


@pytest.mark.parametrize("status,provider_code,expected", [
    (400, "invalid_parameter", "openrouter_bad_request"),
    (401, "invalid_api_key", "openrouter_auth"),
    (403, "permission_denied", "openrouter_permission"),
    (404, "model_not_found", "openrouter_model_unavailable"),
    (500, "server_error", "openrouter_unavailable"),
])
def test_provider_errors_are_specific_redacted_and_not_retried(monkeypatch, status, provider_code, expected):
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(status, json={"error": {"code": provider_code,
                              "message": "sensitive-provider-detail", "type": "test_error"}})

    install_transport(monkeypatch, handler)
    with pytest.raises(DraftError) as caught:
        asyncio.run(generate_answer("Question?", PASSAGES, settings()))
    assert caught.value.code == expected
    assert "sensitive-provider-detail" not in str(caught.value)
    assert "fake-key" not in str(caught.value)
    assert len(requests) == 1


@pytest.mark.parametrize("exc_type,code", [(httpx.ConnectError, "openrouter_connection"),
                                         (httpx.ReadTimeout, "openrouter_timeout")])
def test_transport_failures_are_actionable(monkeypatch, exc_type, code):
    def handler(request):
        raise exc_type("transport-error", request=request)

    install_transport(monkeypatch, handler)
    with pytest.raises(DraftError) as caught:
        asyncio.run(generate_answer("Question?", PASSAGES, settings()))
    assert caught.value.code == code


@pytest.mark.parametrize("text,finish_reason", [("", "stop"), ("Partial", "length")])
def test_empty_or_partial_free_draft_falls_back_before_being_returned(monkeypatch, text, finish_reason):
    requests = []

    def handler(request):
        requests.append(json.loads(request.content))
        if len(requests) == 1:
            return httpx.Response(200, json=completion(text, finish_reason))
        return httpx.Response(200, json=completion("Completed Qwen draft [S1]."))

    install_transport(monkeypatch, handler)
    answer = asyncio.run(generate_answer("Question?", PASSAGES, settings()))
    assert answer == "Completed Qwen draft [S1]."
    assert answer.model == PAID_MODEL
    assert [request["model"] for request in requests] == ["openrouter/free", PAID_MODEL]
    assert requests[1]["provider"] == {"allow_fallbacks": False}
    assert requests[1]["reasoning"] == {"max_tokens": 512}
    assert requests[1]["max_tokens"] == 2400


def test_free_rate_limit_uses_the_fixed_paid_fallback(monkeypatch):
    requests = []

    def handler(request):
        requests.append(request)
        if len(requests) == 1:
            return httpx.Response(429, headers={"retry-after": "18"},
                json={"error": {"code": "rate_limit_exceeded", "message": "limit", "type": "tokens"}})
        return httpx.Response(200, json=completion("Qwen draft [S1]."))

    install_transport(monkeypatch, handler)
    answer = asyncio.run(generate_answer("Question?", PASSAGES, settings()))
    assert answer == "Qwen draft [S1]."
    assert answer.model == PAID_MODEL
    assert len(requests) == 2


def test_paid_fallback_failure_is_actionable_and_not_retried(monkeypatch):
    requests = []

    def handler(request):
        requests.append(request)
        if len(requests) == 1:
            return httpx.Response(429, json={"error": {"code": "rate_limit_exceeded", "message": "limit"}})
        return httpx.Response(500, json={"error": {"code": "server_error", "message": "private failure"}})

    install_transport(monkeypatch, handler)
    with pytest.raises(DraftError) as caught:
        asyncio.run(generate_answer("Question?", PASSAGES, settings()))
    assert caught.value.code == "openrouter_unavailable"
    assert "private failure" not in str(caught.value)
    assert PAID_MODEL in str(caught.value)
    assert len(requests) == 2


def test_groq_fallback_is_used_only_when_explicitly_enabled(monkeypatch):
    monkeypatch.setenv("GROQ_FALLBACK_ENABLED", "true")
    monkeypatch.setenv("GROQ_API_KEY", "groq-test-key")
    requests = []

    def handler(request):
        requests.append(request)
        if len(requests) <= 2:
            return httpx.Response(429, json={"error": {"code": "rate_limit_exceeded", "message": "limit"}})
        return httpx.Response(200, json=completion("Groq draft [S1]."))

    install_transport(monkeypatch, handler)
    answer = asyncio.run(generate_answer("Question?", PASSAGES, settings()))
    assert answer == "Groq draft [S1]."
    assert answer.provider == "groq" and answer.model == "openai/gpt-oss-20b"
    assert requests[0].url.host == "openrouter.ai"
    assert requests[1].url.host == "openrouter.ai"
    assert requests[2].url.host == "api.groq.com"
    assert requests[2].headers["authorization"] == "Bearer groq-test-key"


@pytest.mark.parametrize("name,value", [
    ("OPENROUTER_TIMEOUT_SECONDS", "nan"),
    ("OPENROUTER_TIMEOUT_SECONDS", "120"),
    ("OPENROUTER_MAX_OUTPUT_TOKENS", "wrong"),
    ("OPENROUTER_REASONING_EFFORT", "invalid"),
    ("OPENROUTER_MODEL", "qwen/qwen3.5-flash-02-23"),
    ("OPENROUTER_PAID_FALLBACK_MODEL", "another/paid-model"),
])
def test_bad_settings_fail_before_sending_requests(monkeypatch, name, value):
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "fake-key")
    monkeypatch.setenv(name, value)
    with pytest.raises(DraftError) as caught:
        DraftSettings.from_env()
    assert caught.value.code == "openrouter_config_invalid"


def test_legacy_primary_provider_is_rejected(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "groq-test-key")
    with pytest.raises(DraftError) as caught:
        DraftSettings.from_env()
    assert caught.value.code == "provider_invalid"


def test_vision_request_sends_ephemeral_image_and_recent_history(monkeypatch):
    monkeypatch.setenv("OPENROUTER_VISION_MODEL", VISION_MODEL)
    requests = []

    def handler(request):
        requests.append(json.loads(request.content))
        return httpx.Response(200, json=completion("Mô tả học tập: thấy cấu trúc xương dài rõ bờ."))

    install_transport(monkeypatch, handler)
    answer, used_model = asyncio.run(generate_image_answer(
        "Ảnh này có gì?", b"\xff\xd8\xff\xe0test-jpeg", "image/jpeg", settings(),
        [{"role": "user", "content": "Câu hỏi trước"}],
        trusted_metadata={"image_id": "IMG000001.jpeg", "sites": ["femur"]}))
    assert "cấu trúc xương" in answer
    assert used_model == VISION_MODEL
    payload = requests[0]
    assert payload["model"] == VISION_MODEL
    user_content = payload["messages"][1]["content"]
    assert user_content[1]["type"] == "image_url"
    assert user_content[1]["image_url"]["url"].startswith("data:image/jpeg;base64,")
    prompt = json.loads(user_content[0]["text"])
    assert prompt["recent_conversation"] == [{"role": "user", "content": "Câu hỏi trước"}]
    assert prompt["trusted_dataset_metadata"]["image_id"] == "IMG000001.jpeg"


def test_vision_rate_limit_retries_free_router_then_uses_paid_fallback(monkeypatch):
    monkeypatch.setenv("OPENROUTER_VISION_MODEL", VISION_MODEL)
    requests = []

    def handler(request):
        requests.append(json.loads(request.content))
        if len(requests) <= 2:
            return httpx.Response(429, json={"error": {"code": "rate_limit_exceeded", "message": "limit"}})
        return httpx.Response(200, json=completion("Phân tích ảnh học tập."))

    install_transport(monkeypatch, handler)
    answer, used_model = asyncio.run(generate_image_answer(
        "Mô tả ảnh", b"\xff\xd8\xff\xe0test", "image/jpeg", settings()))
    assert answer == "Phân tích ảnh học tập."
    assert used_model == PAID_MODEL
    assert [item["model"] for item in requests] == [VISION_MODEL, "openrouter/free", PAID_MODEL]
    assert requests[2]["max_tokens"] == 2400
