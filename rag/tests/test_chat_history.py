"""SQLite persistence contract for local text-only chat history."""
from fastapi.testclient import TestClient
import pytest

from rag import chat_history
from rag.demo_api import create_app


def use_temp_database(monkeypatch, tmp_path):
    db_path = tmp_path / "chat_history.db"
    monkeypatch.setattr(chat_history, "DB_PATH", db_path)
    return db_path


def test_turn_round_trip_keeps_only_text_and_allowed_source_fields(monkeypatch, tmp_path):
    db_path = use_temp_database(monkeypatch, tmp_path)
    chat_history.init_db()
    source = {
        "chunk_id": "chunk-1",
        "source_id": "source-1",
        "title": "Review",
        "text": "Passage text",
        "source_sha256": "abc123",
        "patient_age": 52,
        "image_path": "private-xray.png",
    }

    conversation_id = chat_history.save_turn(None, "  Xin chào  ", "  Chào bạn!  ", [source])

    # Reinitialize and reopen, mirroring an application restart.
    chat_history.init_db()
    conversation = chat_history.get_conversation(conversation_id)
    assert conversation["title"] == "Xin chào"
    assert [message["role"] for message in conversation["messages"]] == ["user", "assistant"]
    assert [message["content"] for message in conversation["messages"]] == ["Xin chào", "Chào bạn!"]
    assert conversation["messages"][0]["sources"] == []
    assert conversation["messages"][1]["sources"] == [{
        "chunk_id": "chunk-1", "source_id": "source-1", "title": "Review",
        "text": "Passage text", "source_sha256": "abc123",
    }]
    stored = db_path.read_bytes()
    assert b"private-xray.png" not in stored
    assert b"patient_age" not in stored


def test_conversation_can_be_listed_renamed_and_deleted_with_messages(monkeypatch, tmp_path):
    use_temp_database(monkeypatch, tmp_path)
    chat_history.init_db()
    conversation_id = chat_history.save_turn(None, "Question", "Answer")

    listed = chat_history.list_conversations()
    assert len(listed) == 1
    assert listed[0]["id"] == conversation_id
    assert listed[0]["preview"] == "Answer"
    assert listed[0]["message_count"] == 2

    assert chat_history.rename_conversation(conversation_id, "  Notes  ") is True
    assert chat_history.get_conversation(conversation_id)["title"] == "Notes"
    assert chat_history.delete_conversation(conversation_id) is True
    assert chat_history.get_conversation(conversation_id) is None
    assert chat_history.list_conversations() == []
    assert chat_history.delete_conversation(conversation_id) is False


def test_image_notice_is_kept_in_message_but_not_sidebar_title():
    chat_history.init_db()
    question = "Mô tả ảnh này\n\n[Đã gửi kèm ảnh ngữ cảnh; ảnh không được lưu]"
    cid = chat_history.save_turn(None, question, "Bản nháp")
    conversation = chat_history.get_conversation(cid)
    assert conversation["title"] == "Mô tả ảnh này"
    assert conversation["messages"][0]["content"] == question


def test_message_limit_never_silently_deletes_saved_turns(monkeypatch, tmp_path):
    use_temp_database(monkeypatch, tmp_path)
    monkeypatch.setattr(chat_history, "MAX_MESSAGES_PER_CONVERSATION", 4)
    chat_history.init_db()
    conversation_id = chat_history.save_turn(None, "Q1", "A1")
    chat_history.save_turn(conversation_id, "Q2", "A2")
    with pytest.raises(OverflowError):
        chat_history.save_turn(conversation_id, "Q3", "A3")

    messages = chat_history.get_conversation(conversation_id)["messages"]
    assert [message["content"] for message in messages] == ["Q1", "A1", "Q2", "A2"]


def test_conversation_limit_never_silently_deletes_old_history(monkeypatch, tmp_path):
    use_temp_database(monkeypatch, tmp_path)
    monkeypatch.setattr(chat_history, "MAX_CONVERSATIONS", 1)
    chat_history.init_db()
    first = chat_history.save_turn(None, "Q1", "A1")
    with pytest.raises(OverflowError):
        chat_history.save_turn(None, "Q2", "A2")
    assert chat_history.get_conversation(first)["messages"][1]["content"] == "A1"


def test_http_history_endpoints_persist_across_requests_and_delete_cascade(monkeypatch, tmp_path):
    use_temp_database(monkeypatch, tmp_path)
    with TestClient(create_app(), base_url="http://127.0.0.1:8765") as client:
        saved = client.post("/api/conversations/turn", json={
            "question": "Osteochondroma?", "answer": "See [S1].",
            "sources": [{"source_id": "s1", "title": "Source", "text": "Passage", "extra": "discard"}],
        })
        assert saved.status_code == 200
        conversation_id = saved.json()["conversation_id"]

        listed = client.get("/api/conversations")
        assert listed.status_code == 200
        assert listed.json()["conversations"][0]["id"] == conversation_id

        opened = client.get(f"/api/conversations/{conversation_id}")
        assert opened.status_code == 200
        assert opened.json()["messages"][1]["sources"] == [{
            "source_id": "s1", "title": "Source", "text": "Passage",
        }]

        renamed = client.patch(f"/api/conversations/{conversation_id}", json={"title": "Study notes"})
        assert renamed.status_code == 200
        assert client.get(f"/api/conversations/{conversation_id}").json()["title"] == "Study notes"

        deleted = client.delete(f"/api/conversations/{conversation_id}")
        assert deleted.status_code == 200
        assert deleted.json() == {"deleted": True}
        assert client.get(f"/api/conversations/{conversation_id}").status_code == 404

        # A delayed save from an old browser request must not revive deleted history.
        stale = client.post("/api/conversations/turn", json={
            "conversation_id": conversation_id, "question": "Late question", "answer": "Late answer",
        })
        assert stale.status_code == 409
        assert client.get(f"/api/conversations/{conversation_id}").status_code == 404

