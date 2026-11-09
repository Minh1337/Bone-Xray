"""End-to-end integration test with the real Swin+Metadata checkpoint and real RAG Retriever.

Uses a mocked LLM provider so no external network calls or API keys are required,
while verifying that the actual `model/best_model.pt` and `rag/index/` work
together inside `rag.demo_api`.
"""

import json
from pathlib import Path

from fastapi.testclient import TestClient

from rag.demo_api import create_app


ROOT = Path(__file__).resolve().parents[1]


def test_real_model_and_real_retriever_end_to_end_pipeline(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-only-no-network")
    monkeypatch.setenv("OPENROUTER_MODEL", "openrouter/free")
    monkeypatch.setenv("OPENROUTER_REASONING_EFFORT", "none")
    monkeypatch.setenv("OPENROUTER_TIMEOUT_SECONDS", "35")
    monkeypatch.setenv("OPENROUTER_MAX_OUTPUT_TOKENS", "1600")

    async def fake_explain(record, passages, settings):
        assert len(passages) >= 1
        from rag.generation import DraftText
        return DraftText("### Kết quả mô hình\nTop-1 osteosarcoma.\n### Tài liệu nói gì về khái niệm\nSarcoma xương [S1].\n### Giới hạn\nChỉ học tập.",
                         "openrouter", "openrouter/free")

    monkeypatch.setattr("rag.case_context.explain_case", fake_explain)

    cases_data = json.loads((ROOT / "cases.json").read_text(encoding="utf-8-sig"))
    # case_002 (IMG000002.jpg) has Top-1 = osteosarcoma (status='direct') and Case_001 has Top-1 = other mt (status='aggregate').
    case_osteo = next(c for c in cases_data if c["id"] == "case_002")
    case_agg = next(c for c in cases_data if c["id"] == "case_001")

    with TestClient(create_app(), base_url="http://127.0.0.1:8765") as client:
        # 1. Direct-mapped class (osteosarcoma -> retrieves real passages + explains)
        img2_bytes = (ROOT / case_osteo["image"]).read_bytes()
        r_case2 = client.post(
            "/api/case",
            data={"metadata": json.dumps(case_osteo["metadata"])},
            files={"file": ("IMG000002.jpg", img2_bytes, "image/jpeg")},
        )
        assert r_case2.status_code == 200, r_case2.text
        c2 = r_case2.json()
        assert c2["top1"] == "osteosarcoma"
        assert c2["mapping"]["status"] == "direct"
        assert c2["answer_ready"] is False

        r_exp2 = client.post(f"/api/case/{c2['case_id']}/explain")
        assert r_exp2.status_code == 200
        exp2 = r_exp2.json()
        assert exp2["status"] == "case_explanation"
        assert exp2["basis"] == "documents"
        assert len(exp2["passages"]) >= 1
        assert exp2["answer_ready"] is False

        # 2. Aggregate class (other mt -> deterministic template, no retrieval)
        img1_bytes = (ROOT / case_agg["image"]).read_bytes()
        r_case1 = client.post(
            "/api/case",
            data={"metadata": json.dumps(case_agg["metadata"])},
            files={"file": ("IMG000001.jpg", img1_bytes, "image/jpeg")},
        )
        assert r_case1.status_code == 200
        c1 = r_case1.json()
        assert c1["top1"] == "other mt"
        assert c1["mapping"]["status"] == "aggregate"

        r_exp1 = client.post(f"/api/case/{c1['case_id']}/explain")
        assert r_exp1.status_code == 200
        exp1 = r_exp1.json()
        assert exp1["basis"] == "server_template"
        assert exp1["lookup"] == "not_allowed"
        assert exp1["passages"] == []
        assert exp1["answer_ready"] is False


def test_btxrd_reference_image_lookup_autofill_and_real_model_inference(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-only-no-network")
    monkeypatch.setenv("OPENROUTER_MODEL", "openrouter/free")
    monkeypatch.setenv("OPENROUTER_REASONING_EFFORT", "none")
    monkeypatch.setenv("OPENROUTER_TIMEOUT_SECONDS", "35")
    monkeypatch.setenv("OPENROUTER_MAX_OUTPUT_TOKENS", "1600")

    with TestClient(create_app(), base_url="http://127.0.0.1:8765") as client:
        # 1. Load real BTXRD image by ID -> exact SHA-256 metadata match -> run real Swin+CrossAttention inference
        ref_res = client.get("/api/reference-images/IMG000002")
        assert ref_res.status_code == 200
        assert ref_res.headers["content-type"] == "image/jpeg"

        match_res = client.post(
            "/api/case/metadata-match",
            files={"file": ("IMG000002.jpeg", ref_res.content, "image/jpeg")},
        )
        assert match_res.status_code == 200
        match_body = match_res.json()
        assert match_body["matched"] is True
        assert match_body["image_id"] == "IMG000002.jpeg"
        assert match_body["match_method"] == "sha256_exact"

        case_res = client.post(
            "/api/case",
            data={"metadata": json.dumps(match_body["metadata"])},
            files={"file": ("IMG000002.jpeg", ref_res.content, "image/jpeg")},
        )
        assert case_res.status_code == 200
        case_body = case_res.json()
        assert case_body["top1"] == "osteosarcoma"
        assert case_body["answer_ready"] is False

        # 2. Known duplicate-byte group with conflicting metadata in real BTXRD manifest -> blocked (409)
        dup_res = client.get("/api/reference-images/IMG000430")
        assert dup_res.status_code == 409
