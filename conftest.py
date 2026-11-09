"""Keep automated tests isolated from the developer's local chat database."""
import pytest


@pytest.fixture(autouse=True)
def isolate_chat_history_db(monkeypatch, tmp_path):
    from rag import chat_history

    monkeypatch.setattr(chat_history, "DB_PATH", tmp_path / "chat_history.db")
