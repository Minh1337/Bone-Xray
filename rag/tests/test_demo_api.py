"""Meaningful guard checks for the local source lookup interface."""

from fastapi.testclient import TestClient
from unittest.mock import patch
import time

import pytest

from rag.demo_api import create_app
from rag.generation import DraftError


@pytest.fixture(autouse=True)
def api_settings(monkeypatch):
    # Tests never use credentials from the developer's .env.
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-only-no-network")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5.4-mini")
    monkeypatch.setenv("OPENAI_REASONING_EFFORT", "none")
    monkeypatch.setenv("OPENAI_TIMEOUT_SECONDS", "35")
    monkeypatch.setenv("OPENAI_MAX_OUTPUT_TOKENS", "1600")


def test_rejected_case_never_calls_a_generator_or_returns_passages():
    def rejected(question, top_k):
        assert top_k == 5
        return {"status": "insufficient_evidence", "reason": "image_requires_specialist_assessment",
                "answer_ready": False, "hits": []}

    with TestClient(create_app(rejected), base_url="http://127.0.0.1:8765") as client:
        result = client.post("/api/query", json={"question": "Read my child's X-ray"})
    assert result.status_code == 200
    assert result.json() == {"status": "insufficient_evidence", "reason": "image_requires_specialist_assessment",
                             "answer_ready": False, "passages": []}


def test_fail_closed_if_rejected_question_has_hits_or_answer_ready():
    for answer_ready, hits in [(True, []), (False, [{"text": "not allowed"}])]:
        def invalid(question, top_k):
            return {"status": "out_of_scope", "reason": "scope", "answer_ready": answer_ready,
                    "hits": hits}

        with TestClient(create_app(invalid), base_url="http://127.0.0.1:8765") as client:
            result = client.post("/api/query", json={"question": "Unrelated"})
        assert result.status_code == 503
        assert result.json()["detail"] == "Source lookup unavailable"


def test_other_site_cannot_post_to_local_demo():
    def unexpected(question, top_k):
        raise AssertionError("Cross-origin request reached retrieval")

    with TestClient(create_app(unexpected), base_url="http://127.0.0.1:8765") as client:
        result = client.post("/api/query", json={"question": "Osteochondroma"},
                             headers={"Origin": "https://other.example"})
        bad_host = client.get("/", headers={"Host": "other.example"})
    assert result.status_code == 403
    assert bad_host.status_code == 400


def test_empty_candidate_result_fails_closed():
    def invalid(question, top_k):
        return {"status": "candidates_found", "reason": "unvalidated_candidates",
                "answer_ready": False, "hits": []}

    with TestClient(create_app(invalid), base_url="http://127.0.0.1:8765") as client:
        result = client.post("/api/query", json={"question": "Osteochondroma"})
    assert result.status_code == 503


def test_repeated_queries_reuse_one_checked_retriever():
    engines = []

    def make_engine():
        engine = object()
        engines.append(engine)
        return engine

    def routed(question, *, engine, top_k):
        assert engine is engines[0] and top_k == 5
        return {"status": "out_of_scope", "reason": "outside_bone_tumor_corpus",
                "answer_ready": False, "hits": []}

    with patch("rag.demo_api.retrieval.Retriever", side_effect=make_engine), \
         patch("rag.demo_api.retrieval.retrieve", side_effect=routed):
        with TestClient(create_app(), base_url="http://127.0.0.1:8765") as client:
            for question in ("first query", "second query"):
                response = client.post("/api/query", json={"question": question})
                assert response.status_code == 200
    assert len(engines) == 1


def test_missing_key_fails_before_loading_retrieval_but_greeting_still_works(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY")

    def unexpected(*args, **kwargs):
        raise AssertionError("Missing key must be reported before loading retrieval")

    with TestClient(create_app(unexpected), base_url="http://127.0.0.1:8765") as client:
        response = client.post("/api/query", json={"question": "osteochondroma"})
        greeting = client.post("/api/query", json={"question": "xin chào"})
    assert response.status_code == 503
    assert response.json()["error_code"] == "openai_key_missing"
    assert greeting.status_code == 200
    assert greeting.json()["answer_ready"] is False


def candidates(question, *, top_k):
    hit = {key: "fixture" for key in (
        "chunk_id", "source_id", "title", "publisher", "url", "section",
        "source_date", "license", "source_sha256", "text_sha256", "text"
    )}
    return {"status": "candidates_found", "reason": "unvalidated_candidates",
            "answer_ready": False, "hits": [hit]}


@pytest.mark.parametrize("provider,model", [("openai", "gpt-5.4-mini"), ("groq", "openai/gpt-oss-20b")])
def test_provider_success_preserves_sources_and_unverified_status(monkeypatch, provider, model):
    monkeypatch.setenv("LLM_PROVIDER", provider)
    monkeypatch.setenv(f"{provider.upper()}_API_KEY", "test-only-no-network")

    async def draft(question, passages, settings):
        assert passages[0]["text_sha256"] == "fixture"
        assert settings.model == model
        assert settings.provider == provider
        return "Bản nháp kiểm tra [S1]."

    monkeypatch.setattr("rag.demo_api.generate_answer", draft)
    with TestClient(create_app(candidates), base_url="http://127.0.0.1:8765") as client:
        response = client.post("/api/query", json={"question": "osteochondroma"})
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == provider
    assert data["answer_ready"] is False
    assert data["answer"] == "Bản nháp kiểm tra [S1]."
    assert data["passages"][0]["source_sha256"] == "fixture"


def test_openai_error_returns_actionable_code_without_credentials(monkeypatch):
    async def failed(*args):
        raise DraftError("openai_quota", "Kiểm tra số dư API.", 429)

    monkeypatch.setattr("rag.demo_api.generate_answer", failed)
    with TestClient(create_app(candidates), base_url="http://127.0.0.1:8765") as client:
        response = client.post("/api/query", json={"question": "osteochondroma"})
    assert response.status_code == 429
    assert response.json() == {"detail": "Kiểm tra số dư API.", "error_code": "openai_quota"}
    assert "test-only-no-network" not in response.text
    assert response.headers["cache-control"] == "no-store"


def test_retrieval_deadline_returns_without_waiting_for_worker(monkeypatch):
    monkeypatch.setattr("rag.demo_api.RETRIEVAL_TIMEOUT_SECONDS", .01)

    def slow(question, *, top_k):
        time.sleep(.2)
        return {"status": "out_of_scope", "reason": "fixture", "answer_ready": False, "hits": []}

    with TestClient(create_app(slow), base_url="http://127.0.0.1:8765") as client:
        start = time.monotonic()
        response = client.post("/api/query", json={"question": "osteochondroma"})
        elapsed = time.monotonic() - start
    assert response.status_code == 504
    assert elapsed < .15


@pytest.mark.parametrize("provider", ["groq", "openai"])
def test_config_reports_actual_provider_without_exposing_key(monkeypatch, provider):
    monkeypatch.setenv("LLM_PROVIDER", provider)
    monkeypatch.setenv(f"{provider.upper()}_API_KEY", "private-test-value")
    with TestClient(create_app(), base_url="http://127.0.0.1:8765") as client:
        response = client.get("/api/config")
    assert response.status_code == 200
    assert response.json()["provider"] == provider
    assert response.json()["configured"] is True
    assert "private-test-value" not in response.text
    assert "api_key" not in response.text
    assert response.headers["cache-control"] == "no-store"


def test_groq_missing_key_never_falls_back_to_openai_or_loads_retrieval(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    def unexpected(*args, **kwargs):
        raise AssertionError("No retrieval or automatic provider fallback")

    with TestClient(create_app(unexpected), base_url="http://127.0.0.1:8765") as client:
        config = client.get("/api/config").json()
        response = client.post("/api/query", json={"question": "osteochondroma"})
    assert config["provider_label"] == "Groq"
    assert config["configured"] is False
    assert response.status_code == 503
    assert response.json()["error_code"] == "groq_key_missing"
