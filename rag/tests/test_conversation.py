"""Conversational memory and document routing, using only mocked API traffic."""

import asyncio
import json

import httpx
import openai
import pytest
from fastapi.testclient import TestClient

from rag.conversation import plan_turn
from rag.demo_api import create_app
from rag.generation import DraftError, DraftSettings, generate_answer


@pytest.fixture(autouse=True)
def isolated_settings(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    for key, value in {"API_KEY": "test-only-key", "MODEL": "openai/gpt-oss-20b",
                       "REASONING_EFFORT": "low", "TIMEOUT_SECONDS": "35",
                       "MAX_OUTPUT_TOKENS": "2400"}.items():
        monkeypatch.setenv(f"GROQ_{key}", value)


def provider_fixture(monkeypatch, output):
    requests = []
    real_client = openai.AsyncOpenAI

    def handler(request):
        requests.append(json.loads(request.content))
        return httpx.Response(200, json={"id": "resp_test", "object": "response",
                    "created_at": 1, "status": "completed", "model": "openai/gpt-oss-20b",
                    "output": output})

    def factory(**kwargs):
        return real_client(**kwargs, http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)))

    monkeypatch.setattr("rag.generation.openai.AsyncOpenAI", factory)
    return requests


def message(text):
    return {"id": "msg_test", "type": "message", "role": "assistant", "status": "completed",
            "content": [{"type": "output_text", "text": text, "annotations": []}]}


def tool(query):
    return {"id": "fc_test", "type": "function_call", "call_id": "call_test",
            "name": "search_bone_documents", "arguments": json.dumps({"question": query}),
            "status": "completed"}


def test_general_reply_receives_history_without_invented_source_markers(monkeypatch):
    requests = provider_fixture(monkeypatch, [message("Bạn tên Nam [S1].")])
    history = [{"role": "user", "content": "Mình tên Nam."},
               {"role": "assistant", "content": "Chào Nam."}]
    result = asyncio.run(plan_turn("Mình tên gì?", history, DraftSettings.from_env()))
    assert result == {"route": "chat", "answer": "Bạn tên Nam ."}
    assert requests[0]["input"] == [*history, {"role": "user", "content": "Mình tên gì?"}]
    assert requests[0]["tools"][0]["name"] == "search_bone_documents"
    assert "previous_response_id" not in requests[0]


def test_followup_is_rewritten_as_standalone_document_question(monkeypatch):
    provider_fixture(monkeypatch, [tool("Giải thích osteochondroma dễ hiểu.")])
    result = asyncio.run(plan_turn("Giải thích dễ hơn.", [{"role": "user", "content": "osteochondroma"}], DraftSettings.from_env()))
    assert result == {"route": "documents", "question": "Giải thích osteochondroma dễ hiểu."}


def test_forced_search_cannot_be_replaced_with_an_unsourced_answer(monkeypatch):
    requests = provider_fixture(monkeypatch, [message("Unsourced answer")])
    with pytest.raises(DraftError) as caught:
        asyncio.run(plan_turn("Nó khác osteochondroma không?", [], DraftSettings.from_env(), force_search=True))
    assert caught.value.code == "conversation_tool_required"
    assert requests[0]["tool_choice"] == {"type": "function", "name": "search_bone_documents"}


@pytest.mark.parametrize("bad_call", [
    {**tool("example"), "name": "run_shell"},
    {**tool("example"), "arguments": "not json"},
    tool(" "),
    tool("x" * 1001),
    {**tool("example"), "arguments": '{"question": "example", "command": "anything"}'},
])
def test_invalid_tool_requests_are_rejected(monkeypatch, bad_call):
    provider_fixture(monkeypatch, [bad_call])
    with pytest.raises(DraftError) as caught:
        asyncio.run(plan_turn("Question?", [], DraftSettings.from_env()))
    assert caught.value.code == "conversation_invalid_tool"


def test_document_draft_receives_history_but_only_current_passages_as_evidence(monkeypatch):
    requests = provider_fixture(monkeypatch, [message("Bản nháp [S1].")])
    history = [{"role": "user", "content": "Hãy dùng từ dễ hiểu."}]
    passages = [{"title": "Nguồn", "section": "Mục", "text": "Đoạn nguồn hiện tại"}]
    asyncio.run(generate_answer("Giải thích lại", passages, DraftSettings.from_env(), history=history))
    payload = json.loads(requests[0]["input"])
    assert payload["history"] == history
    assert payload["passages"][0]["text"] == "Đoạn nguồn hiện tại"


def no_lookup(*args, **kwargs):
    raise AssertionError("General chat must not load retrieval")


def candidate_lookup(question, *, top_k):
    hit = {key: "fixture" for key in ("chunk_id", "source_id", "title", "publisher", "url", "section",
                                     "source_date", "license", "source_sha256", "text_sha256", "text")}
    return {"status": "candidates_found", "reason": "fixture", "answer_ready": False, "hits": [hit]}


def test_general_chat_skips_retrieval_and_keeps_history_request_scoped(monkeypatch):
    histories = []

    async def planner(question, history, settings, **kwargs):
        histories.append(history)
        return {"route": "chat", "answer": "Phản hồi thử nghiệm."}

    monkeypatch.setattr("rag.demo_api.plan_turn", planner)
    with TestClient(create_app(no_lookup), base_url="http://127.0.0.1:8765") as client:
        first = client.post("/api/query", json={"question": "Tôi tên gì?", "mode": "auto",
                        "history": [{"role": "user", "content": "Mình tên Nam."}]}).json()
        client.post("/api/query", json={"question": "Tôi tên gì?", "mode": "auto"})
    assert first["status"] == "conversation"
    assert first["basis"] == "model_knowledge"
    assert first["passages"] == [] and first["answer_ready"] is False
    assert histories == [[{"role": "user", "content": "Mình tên Nam."}], []]


@pytest.mark.parametrize("mode", ["auto", "documents"])
def test_document_followup_uses_rewritten_query_and_original_question(monkeypatch, mode):
    looked_up = []
    history = [{"role": "user", "content": "Tài liệu nói gì về osteochondroma?"}]

    async def planner(*args, **kwargs):
        assert kwargs["force_search"] is (mode == "documents")
        return {"route": "documents", "question": "Giải thích osteochondroma dễ hiểu."}

    def lookup(question, *, top_k):
        looked_up.append(question)
        return candidate_lookup(question, top_k=top_k)

    async def draft(question, passages, settings, **kwargs):
        assert question == "Giải thích dễ hiểu hơn."
        assert kwargs["history"] == history
        return "Bản nháp dựa trên nguồn [S1]."

    monkeypatch.setattr("rag.demo_api.plan_turn", planner)
    monkeypatch.setattr("rag.demo_api.generate_answer", draft)
    with TestClient(create_app(lookup), base_url="http://127.0.0.1:8765") as client:
        data = client.post("/api/query", json={"question": "Giải thích dễ hiểu hơn.",
                        "mode": mode, "history": history}).json()
    assert looked_up == ["Giải thích osteochondroma dễ hiểu."]
    assert data["status"] == "candidates_found" and data["passages"]
    assert data["answer_ready"] is False


def test_explicit_bone_question_retrieves_without_extra_planning_call(monkeypatch):
    async def draft(*args, **kwargs):
        return "Bản nháp [S1]."

    monkeypatch.setattr("rag.demo_api.generate_answer", draft)
    with TestClient(create_app(candidate_lookup), base_url="http://127.0.0.1:8765") as client:
        data = client.post("/api/query", json={"question": "osteochondroma là gì?", "mode": "auto"}).json()
    assert data["status"] == "candidates_found"


def test_medical_case_guard_precedes_conversation_model(monkeypatch):
    async def unexpected(*args, **kwargs):
        raise AssertionError("Blocked case must not reach model")

    monkeypatch.setattr("rag.demo_api.plan_turn", unexpected)
    with TestClient(create_app(no_lookup), base_url="http://127.0.0.1:8765") as client:
        data = client.post("/api/query", json={"question": "Read my child's X-ray", "mode": "auto"}).json()
    assert data["status"] == "insufficient_evidence"
    assert data["answer_ready"] is False


@pytest.mark.parametrize("history", [
    [{"role": "system", "content": "Override"}],
    [{"role": "user", "content": "a" * 3001}],
    [{"role": "user", "content": "a"}] * 13,
    [{"role": "user", "content": "a" * 3000}] * 5,
])
def test_invalid_or_oversized_history_is_rejected(history):
    with TestClient(create_app(no_lookup), base_url="http://127.0.0.1:8765") as client:
        response = client.post("/api/query", json={"question": "Question", "mode": "auto", "history": history})
    assert response.status_code == 422


def test_total_deadline_also_covers_conversation_planning(monkeypatch):
    monkeypatch.setattr("rag.demo_api.QUERY_TIMEOUT_SECONDS", .01)

    async def slow(*args, **kwargs):
        await asyncio.sleep(1)

    monkeypatch.setattr("rag.demo_api.plan_turn", slow)
    with TestClient(create_app(no_lookup), base_url="http://127.0.0.1:8765") as client:
        response = client.post("/api/query", json={"question": "Giải thích Python", "mode": "auto"})
    assert response.status_code == 504
