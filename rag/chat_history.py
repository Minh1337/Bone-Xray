"""Local SQLite persistence for completed text conversations and citations."""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "chat_history.db"
MAX_CONVERSATIONS = 500
MAX_MESSAGES_PER_CONVERSATION = 2000
SOURCE_FIELDS = ("chunk_id", "source_id", "title", "publisher", "url", "section",
                 "source_date", "license", "source_sha256", "text_sha256", "text")


def now():
    return datetime.now(timezone.utc).isoformat()


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    return db


def init_db():
    with connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS conversations (
          id TEXT PRIMARY KEY, title TEXT NOT NULL, created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS messages (
          id INTEGER PRIMARY KEY AUTOINCREMENT, conversation_id TEXT NOT NULL
            REFERENCES conversations(id) ON DELETE CASCADE,
          role TEXT NOT NULL CHECK(role IN ('user','assistant')), content TEXT NOT NULL,
          sources_json TEXT NOT NULL DEFAULT '[]', created_at TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS idx_chat_updated ON conversations(updated_at DESC);
        CREATE INDEX IF NOT EXISTS idx_chat_messages ON messages(conversation_id,id);
        """)


def list_conversations(limit=MAX_CONVERSATIONS):
    with connect() as db:
        rows = db.execute("""SELECT c.id,c.title,c.created_at,c.updated_at,
          (SELECT content FROM messages m WHERE m.conversation_id=c.id ORDER BY id DESC LIMIT 1) preview,
          (SELECT COUNT(*) FROM messages m WHERE m.conversation_id=c.id) message_count
          FROM conversations c ORDER BY c.updated_at DESC LIMIT ?""", (limit,)).fetchall()
    return [dict(row) for row in rows]


def get_conversation(cid):
    with connect() as db:
        conv = db.execute("SELECT id,title,created_at,updated_at FROM conversations WHERE id=?", (cid,)).fetchone()
        if conv is None:
            return None
        messages = db.execute("SELECT id,role,content,sources_json,created_at FROM messages WHERE conversation_id=? ORDER BY id", (cid,)).fetchall()
    result = dict(conv)
    result["messages"] = [{"id": m["id"], "role": m["role"], "content": m["content"],
                            "sources": json.loads(m["sources_json"]), "created_at": m["created_at"]}
                           for m in messages]
    return result


def save_turn(cid, question, answer, sources=()):
    conversation_id, _ = save_turn_with_message_id(cid, question, answer, sources)
    return conversation_id


def save_turn_with_message_id(cid, question, answer, sources=()):
    question = question.strip()
    answer = answer.strip()
    timestamp = now()
    is_new = cid is None
    cid = cid or uuid.uuid4().hex
    safe_sources = [{k: source[k] for k in SOURCE_FIELDS if k in source}
                    for source in sources if isinstance(source, dict)]
    with connect() as db:
        existing = db.execute("SELECT id FROM conversations WHERE id=?", (cid,)).fetchone()
        if existing is None:
            if not is_new:
                raise LookupError("Conversation no longer exists")
            count = db.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
            if count >= MAX_CONVERSATIONS:
                raise OverflowError("Conversation history is full")
            # Use the first paragraph so the image-history notice appended by
            # the client is not included in the conversation's sidebar title.
            first_paragraph = question.replace("\r\n", "\n").split("\n\n", 1)[0]
            title = " ".join(first_paragraph.split())[:72] or "Cuộc trò chuyện mới"
            if title == "[Đã gửi kèm ảnh ngữ cảnh; ảnh không được lưu]":
                title = "Ảnh đính kèm"
            db.execute("INSERT INTO conversations VALUES(?,?,?,?)", (cid, title, timestamp, timestamp))
        count = db.execute("SELECT COUNT(*) FROM messages WHERE conversation_id=?", (cid,)).fetchone()[0]
        if count + 2 > MAX_MESSAGES_PER_CONVERSATION:
            raise OverflowError("Conversation has reached the message limit")
        insert = "INSERT INTO messages(conversation_id,role,content,sources_json,created_at) VALUES(?,?,?,?,?)"
        message_id = db.execute(insert, (cid, "user", question[:3000], "[]", timestamp)).lastrowid
        db.execute(insert, (cid, "assistant", answer[:12000], json.dumps(safe_sources, ensure_ascii=False), timestamp))
        db.execute("UPDATE conversations SET updated_at=? WHERE id=?", (timestamp, cid))
    return cid, message_id


def rename_conversation(cid, title):
    with connect() as db:
        cur = db.execute("UPDATE conversations SET title=?,updated_at=? WHERE id=?", (title.strip()[:100], now(), cid))
        return cur.rowcount > 0


def delete_conversation(cid):
    with connect() as db:
        cur = db.execute("DELETE FROM conversations WHERE id=?", (cid,))
        return cur.rowcount > 0
