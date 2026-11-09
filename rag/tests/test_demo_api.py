"""Meaningful guard checks for the local source lookup interface."""

from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import time
from io import BytesIO
from hashlib import sha256

from PIL import Image

import pytest

from rag.demo_api import create_app
from rag.generation import DraftError


def test_reference_image_loads_from_catalogue_and_matches_metadata(monkeypatch, tmp_path):
    import rag.demo_api as api

    output = BytesIO()
    Image.new("RGB", (4, 4), "white").save(output, format="JPEG")
    raw = output.getvalue()
    source = tmp_path / "data" / "external_datasets" / "BTXRD" / "reference" / "source"
    image = source / "BTXRD" / "images" / "IMG000001.jpeg"
    image.parent.mkdir(parents=True)
    image.write_bytes(raw)
    metadata = {"age": 48, "gender": "F", "frontal": 1}
    monkeypatch.setattr(api, "ROOT", tmp_path)
    monkeypatch.setattr(api, "btxrd_hash_index", lambda: {
        sha256(raw).hexdigest(): [{"image_id": "IMG000001.jpeg", "metadata": metadata,
                                   "ground_truth": "other mt",
                                   "relative_path": "BTXRD/images/IMG000001.jpeg"}]
    })
    with TestClient(create_app(lambda *_args, **_kwargs: None), base_url="http://127.0.0.1:8765") as client:
        loaded = client.get("/api/reference-images/IMG000001")
        matched = client.post("/api/case/metadata-match",
                              files={"file": ("IMG000001.jpeg", loaded.content, "image/jpeg")})
        invalid = client.get("/api/reference-images/../../secrets")
    assert loaded.status_code == 200 and loaded.content == raw
    assert loaded.headers["cache-control"] == "no-store"
    assert matched.status_code == 200
    assert matched.json()["metadata"] == metadata
    assert matched.json()["match_method"] == "sha256_exact"
    assert invalid.status_code == 404


def test_duplicate_bytes_with_conflicting_metadata_never_autofill(monkeypatch, tmp_path):
    import rag.demo_api as api

    raw = b"same image bytes"
    first = {"image_id": "IMG000430.jpeg", "metadata": {"age": 20},
             "ground_truth": None, "relative_path": "BTXRD/images/IMG000430.jpeg"}
    second = {**first, "image_id": "IMG000765.jpeg", "metadata": {"age": 42}}
    monkeypatch.setattr(api, "ROOT", tmp_path)
    monkeypatch.setattr(api, "btxrd_hash_index", lambda: {sha256(raw).hexdigest(): [first, second]})
    with TestClient(create_app(lambda *_args, **_kwargs: None), base_url="http://127.0.0.1:8765") as client:
        matched = client.post("/api/case/metadata-match",
                              files={"file": ("IMG000430.jpeg", raw, "image/jpeg")})
        loaded = client.get("/api/reference-images/IMG000430")
    assert matched.json() == {"matched": False, "reason": "ambiguous_metadata"}
    assert loaded.status_code == 409


def test_image_chat_returns_unverified_text_without_persisting_image():
    from rag import chat_history

    output = BytesIO()
    Image.new("RGB", (4, 4), "white").save(output, format="JPEG")
    raw = output.getvalue()
    generated = AsyncMock(return_value=("Quan sát được ảnh sáng; chưa xác định bệnh.", "vision-test"))
    lookups = []

    def retrieve(question, *, top_k):
        lookups.append((question, top_k))
        hit = {key: "fixture" for key in (
            "chunk_id", "source_id", "title", "publisher", "url", "section",
            "source_date", "license", "source_sha256", "text_sha256", "text"
        )}
        hit["title"] = "Nguồn đọc thêm về ảnh xương"
        return {"status": "candidates_found", "reason": "unvalidated_candidates",
                "answer_ready": False, "hits": [hit]}

    with patch("rag.demo_api.generate_image_answer", generated):
        with TestClient(create_app(retrieve),
                        base_url="http://127.0.0.1:8765") as client:
            result = client.post("/api/image-chat", data={"question": "Ảnh này có gì?"},
                                 files={"file": ("study.jpg", raw, "image/jpeg")})
            bad = client.post("/api/image-chat", data={"question": "Ảnh này có gì?"},
                              files={"file": ("fake.jpg", b"not an image", "image/jpeg")})
    assert result.status_code == 200
    assert result.json()["answer_ready"] is False
    assert result.json()["image_not_stored"] is True
    assert result.json()["source_lookup_status"] == "candidates_found"
    assert result.json()["passages"][0]["title"] == "Nguồn đọc thêm về ảnh xương"
    assert lookups[0][0].startswith("Ảnh này có gì?\nQuan sát được ảnh sáng")
    assert lookups[0][1] == 4
    assert generated.await_count == 1
    assert generated.await_args.args[1] == raw
    assert bad.status_code == 415
    assert chat_history.list_conversations() == []
    assert raw not in chat_history.DB_PATH.read_bytes()


@pytest.fixture(autouse=True)
def api_settings(monkeypatch):
    # Tests never use credentials from the developer's .env.
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-only-no-network")
    monkeypatch.setenv("OPENROUTER_MODEL", "openrouter/free")
    monkeypatch.setenv("OPENROUTER_REASONING_EFFORT", "none")
    monkeypatch.setenv("OPENROUTER_TIMEOUT_SECONDS", "35")
    monkeypatch.setenv("OPENROUTER_MAX_OUTPUT_TOKENS", "1600")


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
    monkeypatch.delenv("OPENROUTER_API_KEY")

    def unexpected(*args, **kwargs):
        raise AssertionError("Missing key must be reported before loading retrieval")

    with TestClient(create_app(unexpected), base_url="http://127.0.0.1:8765") as client:
        response = client.post("/api/query", json={"question": "osteochondroma"})
        greeting = client.post("/api/query", json={"question": "xin chào"})
    assert response.status_code == 503
    assert response.json()["error_code"] == "openrouter_key_missing"
    assert greeting.status_code == 200
    assert greeting.json()["answer_ready"] is False


def candidates(question, *, top_k):
    hit = {key: "fixture" for key in (
        "chunk_id", "source_id", "title", "publisher", "url", "section",
        "source_date", "license", "source_sha256", "text_sha256", "text"
    )}
    return {"status": "candidates_found", "reason": "unvalidated_candidates",
            "answer_ready": False, "hits": [hit]}


def test_openrouter_success_preserves_sources_and_unverified_status(monkeypatch):
    provider, model = "openrouter", "openrouter/free"
    monkeypatch.setenv("LLM_PROVIDER", provider)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-only-no-network")

    async def draft(question, passages, settings):
        from rag.generation import DraftText
        assert passages[0]["text_sha256"] == "fixture"
        assert settings.model == model
        assert settings.provider == provider
        return DraftText("Bản nháp kiểm tra [S1].", provider, model)

    monkeypatch.setattr("rag.demo_api.generate_answer", draft)
    with TestClient(create_app(candidates), base_url="http://127.0.0.1:8765") as client:
        response = client.post("/api/query", json={"question": "osteochondroma"})
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == provider
    assert data["answer_ready"] is False
    assert data["answer"] == "Bản nháp kiểm tra [S1]."
    assert data["passages"][0]["source_sha256"] == "fixture"


def test_openrouter_error_returns_actionable_code_without_credentials(monkeypatch):
    async def failed(*args):
        raise DraftError("openrouter_rate_limit", "Kiểm tra giới hạn OpenRouter.", 429)

    monkeypatch.setattr("rag.demo_api.generate_answer", failed)
    with TestClient(create_app(candidates), base_url="http://127.0.0.1:8765") as client:
        response = client.post("/api/query", json={"question": "osteochondroma"})
    assert response.status_code == 429
    assert response.json() == {"detail": "Kiểm tra giới hạn OpenRouter.", "error_code": "openrouter_rate_limit"}
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


def test_config_reports_openrouter_without_exposing_key(monkeypatch):
    provider = "openrouter"
    monkeypatch.setenv("LLM_PROVIDER", provider)
    monkeypatch.setenv("OPENROUTER_API_KEY", "private-test-value")
    with TestClient(create_app(), base_url="http://127.0.0.1:8765") as client:
        response = client.get("/api/config")
    assert response.status_code == 200
    assert response.json()["provider"] == provider
    assert response.json()["configured"] is True
    assert "private-test-value" not in response.text
    assert "api_key" not in response.text
    assert response.headers["cache-control"] == "no-store"


def test_groq_cannot_be_selected_as_primary_provider(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "groq")

    def unexpected(*args, **kwargs):
        raise AssertionError("An unsupported provider must fail before retrieval")

    with TestClient(create_app(unexpected), base_url="http://127.0.0.1:8765") as client:
        config = client.get("/api/config").json()
        response = client.post("/api/query", json={"question": "osteochondroma"})
    assert config["provider"] is None
    assert config["configured"] is False
    assert response.status_code == 503
    assert response.json()["error_code"] == "provider_invalid"
