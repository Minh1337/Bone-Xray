"""Meaningful guard checks for the local source lookup interface."""

from fastapi.testclient import TestClient
from unittest.mock import patch

from rag.demo_api import create_app


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
