"""Tests for educational image-case analysis, label mapping, and chatbot integration."""

import io
import json
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image
import pytest

from api_validation import META_COLS
from rag import case_context as cases
from rag.demo_api import create_app
from rag.generation import DraftError
from xray_api import LABELS


@pytest.fixture(autouse=True)
def isolated_env(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-only-no-network")
    monkeypatch.setenv("OPENROUTER_MODEL", "openrouter/free")
    monkeypatch.setenv("OPENROUTER_REASONING_EFFORT", "none")
    monkeypatch.setenv("OPENROUTER_TIMEOUT_SECONDS", "35")
    monkeypatch.setenv("OPENROUTER_MAX_OUTPUT_TOKENS", "1600")


def make_png_bytes():
    buf = io.BytesIO()
    Image.new("RGB", (24, 24), color=(120, 120, 120)).save(buf, format="PNG")
    return buf.getvalue()


def valid_meta(**overrides):
    meta = {k: 0 for k in META_COLS}
    meta.update({"age": 19, "gender": "M", "femur": 1, "lower limb": 1, "frontal": 1})
    meta.update(overrides)
    return meta


def make_fake_loader(top1_label="osteochondroma", fail_predict=False, fail_load=False):
    assert top1_label in LABELS
    state = {"loads": 0, "paths": []}

    class FakePredictor:
        def predict(self, path, metadata):
            state["paths"].append(Path(path))
            if fail_predict:
                raise RuntimeError("predictor boom")
            rem = 0.18 / (len(LABELS) - 1)
            return [{"label": label, "score": 0.82 if label == top1_label else rem}
                    for label in LABELS]

    def loader():
        state["loads"] += 1
        if fail_load:
            raise RuntimeError("missing checkpoint")
        return FakePredictor(), {"device": "cpu", "sha256": {"best_model.pt": "sha_test_model"}, "labels": LABELS}

    return loader, state


def fake_retrieve(question, *, top_k):
    assert top_k == 5
    hit = {
        "chunk_id": "chunk_osteo_1",
        "source_id": "nci-osteochondroma-definition",
        "title": "NCI Osteochondroma",
        "publisher": "NCI",
        "url": "https://www.cancer.gov/types/bone",
        "section": "Overview",
        "source_date": "2025-01-01",
        "license": "Public Domain",
        "source_sha256": "src_hash_123",
        "text_sha256": "txt_hash_456",
        "text": "Osteochondroma is a benign bone tumor that usually forms near the growth plate.",
    }
    return {"status": "candidates_found", "reason": "unvalidated_candidates",
            "answer_ready": False, "hits": [hit]}


def test_label_guide_covers_all_10_checkpoint_labels_and_matches_retrieval_config():
    assert set(cases.LABEL_GUIDE) == set(LABELS)
    from rag import retrieval
    cfg = retrieval.load_config()
    unsupported = set(cfg["unsupported_terms"])
    for label, spec in cases.LABEL_GUIDE.items():
        assert spec["status"] in {"direct", "unresolved", "aggregate", "no_tumor"}
        if spec["status"] == "direct":
            assert label in cfg["supported_terms"]
            assert spec.get("query")
        else:
            normalized = label.replace("-", " ")
            assert normalized in unsupported


def test_case_upload_validates_demo_metadata_rules_and_cleans_up_temp_image():
    loader, state = make_fake_loader("osteochondroma")
    png = make_png_bytes()
    with TestClient(create_app(fake_retrieve, loader), base_url="http://127.0.0.1:8765") as client:
        # Missing anatomical site (all zeros except frontal=1) -> rejected with 422
        no_site = valid_meta(**{"femur": 0, "lower limb": 0})
        r1 = client.post("/api/case", data={"metadata": json.dumps(no_site)},
                         files={"file": ("patient_secret_name.png", png, "image/png")})
        assert r1.status_code == 422
        assert "vị trí" in r1.json()["detail"]

        # Two radiographic views selected -> rejected with 422
        two_views = valid_meta(frontal=1, lateral=1)
        r2 = client.post("/api/case", data={"metadata": json.dumps(two_views)},
                         files={"file": ("sample.png", png, "image/png")})
        assert r2.status_code == 422
        assert "tư thế" in r2.json()["detail"]

        # Valid case -> 200, opaque case_id, answer_ready=False, temp file deleted
        r3 = client.post("/api/case", data={"metadata": json.dumps(valid_meta())},
                         files={"file": ("patient_secret_name.png", png, "image/png")})
        assert r3.status_code == 200
        body = r3.json()
        assert body["answer_ready"] is False
        assert body["top1"] == "osteochondroma"
        assert body["mapping"]["status"] == "direct"
        assert len(body["top3"]) == 3
        assert "patient_secret_name" not in r3.text
        assert state["loads"] == 1
        assert all(not p.exists() for p in state["paths"])


def test_direct_label_explain_retrieves_sources_and_keeps_privacy_boundaries(monkeypatch):
    loader, _ = make_fake_loader("osteochondroma")
    sent_payloads = []

    async def fake_explain(record, passages, settings):
        ctx = cases.llm_context(record)
        sent_payloads.append({"case_context": ctx, "passages": passages})
        from rag.generation import DraftText
        return DraftText("### Kết quả mô hình\nTop-1 osteochondroma.\n### Tài liệu nói gì về khái niệm\nU lành [S1].\n### Giới hạn\nChỉ học tập.",
                         "openrouter", "openrouter/free")

    monkeypatch.setattr("rag.case_context.explain_case", fake_explain)
    with TestClient(create_app(fake_retrieve, loader), base_url="http://127.0.0.1:8765") as client:
        created = client.post("/api/case", data={"metadata": json.dumps(valid_meta(age=47, gender="F"))},
                              files={"file": ("Private_Patient_01.png", make_png_bytes(), "image/png")}).json()
        explained = client.post(f"/api/case/{created['case_id']}/explain")
    assert explained.status_code == 200
    data = explained.json()
    assert data["status"] == "case_explanation"
    assert data["basis"] == "documents"
    assert data["answer_ready"] is False
    assert len(data["passages"]) == 1
    assert "[S1]" in data["answer"]
    # Privacy check: LLM context only contains Top-3 labels/scores and mapping note, never age/gender/filename/hashes.
    serialized = json.dumps(sent_payloads[0]["case_context"])
    assert "47" not in serialized
    assert "Private_Patient_01" not in serialized
    assert "sha_test_model" not in serialized


@pytest.mark.parametrize("top1_label,expected_status,related", [
    ("osteofibroma", "unresolved", "osteofibrous dysplasia"),
    ("synovial osteochondroma", "unresolved", "synovial chondromatosis"),
    ("multiple osteochondromas", "unresolved", "osteochondroma"),
    ("other bt", "aggregate", None),
    ("other mt", "aggregate", None),
    ("no-tumor", "no_tumor", None),
])
def test_non_direct_labels_never_auto_retrieve_or_call_llm(monkeypatch, top1_label, expected_status, related):
    loader, _ = make_fake_loader(top1_label)

    def forbidden_retrieve(*args, **kwargs):
        raise AssertionError("Retrieval must not run for unresolved/aggregate/no-tumor labels")

    async def forbidden_explain(*args, **kwargs):
        raise AssertionError("LLM must not run when automatic lookup is not allowed")

    monkeypatch.setattr("rag.case_context.explain_case", forbidden_explain)
    with TestClient(create_app(forbidden_retrieve, loader), base_url="http://127.0.0.1:8765") as client:
        created = client.post("/api/case", data={"metadata": json.dumps(valid_meta())},
                              files={"file": ("img.png", make_png_bytes(), "image/png")}).json()
        assert created["mapping"]["status"] == expected_status
        explained = client.post(f"/api/case/{created['case_id']}/explain").json()
    assert explained["status"] == "case_explanation"
    assert explained["basis"] == "server_template"
    assert explained["lookup"] == "not_allowed"
    assert explained["passages"] == []
    assert explained["answer_ready"] is False
    if related:
        assert related in explained["answer"]


def test_explain_falls_back_to_template_with_sources_if_llm_fails(monkeypatch):
    loader, _ = make_fake_loader("osteochondroma")

    async def broken_llm(*args, **kwargs):
        raise DraftError("openrouter_rate_limit", "OpenRouter Free đang giới hạn lượt gọi.", 429)

    monkeypatch.setattr("rag.case_context.explain_case", broken_llm)
    with TestClient(create_app(fake_retrieve, loader), base_url="http://127.0.0.1:8765") as client:
        created = client.post("/api/case", data={"metadata": json.dumps(valid_meta())},
                              files={"file": ("img.png", make_png_bytes(), "image/png")}).json()
        explained = client.post(f"/api/case/{created['case_id']}/explain")
    assert explained.status_code == 200
    body = explained.json()
    assert body["basis"] == "server_template"
    assert len(body["passages"]) == 1
    assert "OpenRouter Free đang giới hạn" in body["draft_error"]
    assert body["answer_ready"] is False


def test_followup_query_uses_server_owned_case_and_rejects_client_score_injection(monkeypatch):
    loader, _ = make_fake_loader("simple bone cyst")
    captured = {}

    async def fake_plan(question, history, settings, *, force_search=False, case_context=None, extra_instructions=""):
        captured["case_context"] = case_context
        return {"route": "chat", "answer": "Nhãn Top-1 của ca đang mở là simple bone cyst (điểm 0.82).",
                "provider": "openrouter", "model": "openrouter/free"}

    monkeypatch.setattr("rag.demo_api.plan_turn", fake_plan)
    with TestClient(create_app(fake_retrieve, loader), base_url="http://127.0.0.1:8765") as client:
        created = client.post("/api/case", data={"metadata": json.dumps(valid_meta())},
                              files={"file": ("img.png", make_png_bytes(), "image/png")}).json()
        cid = created["case_id"]
        reply = client.post("/api/query", json={
            "question": "Giải thích ý nghĩa điểm Top-1 của ca đang mở",
            "mode": "auto",
            "case_id": cid,
        })
        assert reply.status_code == 200
        assert reply.json()["case_context_used"] is True
        assert captured["case_context"]["model_output_top3"][0]["label"] == "simple bone cyst"

        # Deleting/switching the case invalidates the old case_id (410 Gone)
        deleted = client.delete(f"/api/case/{cid}")
        assert deleted.status_code == 200 and deleted.json() == {"deleted": True}
        stale = client.post("/api/query", json={
            "question": "Còn ca đó thì sao?",
            "mode": "auto",
            "case_id": cid,
        })
        assert stale.status_code == 410


def test_cross_origin_and_model_load_failure_are_handled_cleanly():
    loader, _ = make_fake_loader("osteochondroma", fail_load=True)
    with TestClient(create_app(fake_retrieve, loader), base_url="http://127.0.0.1:8765") as client:
        cross = client.post("/api/case", data={"metadata": json.dumps(valid_meta())},
                            files={"file": ("img.png", make_png_bytes(), "image/png")},
                            headers={"Origin": "https://evil.example"})
        assert cross.status_code == 403
        unloaded = client.post("/api/case", data={"metadata": json.dumps(valid_meta())},
                               files={"file": ("img.png", make_png_bytes(), "image/png")})
        assert unloaded.status_code == 503
        assert "mô hình" in unloaded.json()["detail"].lower()
