"""SQLite database for case management.

Tables:
    cases       — prediction results saved by the user
    comments    — free-text notes attached to a case
    corrections — label corrections (stored separately, never overwrite predictions)
"""
import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parent / 'data' / 'bonescope.db'

# ---------------------------------------------------------------------------
# Connection helpers
# ---------------------------------------------------------------------------

def _ensure_dir():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def _connect() -> sqlite3.Connection:
    _ensure_dir()
    conn = sqlite3.connect(str(DB_PATH), timeout=10)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA foreign_keys=ON')
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db():
    """Yield a connection, commit on success, rollback on error."""
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_SCHEMA = """
CREATE TABLE IF NOT EXISTS cases (
    id              TEXT PRIMARY KEY,
    created_at      TEXT NOT NULL,
    image_filename  TEXT NOT NULL,
    image_sha256    TEXT NOT NULL,
    metadata_json   TEXT NOT NULL,
    scores_json     TEXT NOT NULL,
    top1_label      TEXT NOT NULL,
    top1_score      REAL NOT NULL,
    prediction_seconds REAL NOT NULL,
    device          TEXT NOT NULL,
    model_sha256    TEXT NOT NULL,
    api_version     TEXT NOT NULL,
    true_label      TEXT
);

CREATE TABLE IF NOT EXISTS comments (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id     TEXT NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    created_at  TEXT NOT NULL,
    content     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS corrections (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id         TEXT NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    created_at      TEXT NOT NULL,
    corrected_label TEXT NOT NULL,
    reason          TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_comments_case   ON comments(case_id);
CREATE INDEX IF NOT EXISTS idx_corrections_case ON corrections(case_id);
CREATE INDEX IF NOT EXISTS idx_cases_created    ON cases(created_at);
CREATE INDEX IF NOT EXISTS idx_cases_top1       ON cases(top1_label);
"""


def init_db():
    """Create tables if they don't exist.  Safe to call multiple times."""
    with get_db() as conn:
        conn.executescript(_SCHEMA)


# ---------------------------------------------------------------------------
# CRUD — Cases
# ---------------------------------------------------------------------------

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_to_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    # Deserialise JSON columns
    for key in ('metadata_json', 'scores_json'):
        if key in d and isinstance(d[key], str):
            d[key] = json.loads(d[key])
    return d


def save_case(data: dict) -> dict:
    """Insert a new case and return the stored record."""
    case_id = uuid.uuid4().hex[:12]
    now = _now()
    with get_db() as conn:
        conn.execute(
            """INSERT INTO cases
               (id, created_at, image_filename, image_sha256,
                metadata_json, scores_json, top1_label, top1_score,
                prediction_seconds, device, model_sha256, api_version, true_label)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                case_id, now,
                data['image_filename'],
                data['image_sha256'],
                json.dumps(data['metadata'], ensure_ascii=False),
                json.dumps(data['scores'], ensure_ascii=False),
                data['top1'],
                data['top1_score'],
                data['prediction_seconds'],
                data['device'],
                data['model_sha256'],
                data.get('api_version', '0.1.0'),
                data.get('true_label'),
            ),
        )
    return get_case(case_id)


def get_case(case_id: str) -> dict | None:
    with get_db() as conn:
        row = conn.execute('SELECT * FROM cases WHERE id=?', (case_id,)).fetchone()
    return _row_to_dict(row) if row else None


def list_cases(
    *,
    limit: int = 50,
    offset: int = 0,
    label: str | None = None,
) -> dict:
    """Return paginated case list with total count."""
    where = ''
    params: list[Any] = []
    if label:
        where = 'WHERE top1_label=?'
        params.append(label)

    with get_db() as conn:
        total = conn.execute(
            f'SELECT COUNT(*) FROM cases {where}', params
        ).fetchone()[0]

        rows = conn.execute(
            f'SELECT * FROM cases {where} ORDER BY created_at DESC LIMIT ? OFFSET ?',
            params + [limit, offset],
        ).fetchall()

    return {
        'total': total,
        'limit': limit,
        'offset': offset,
        'cases': [_row_to_dict(r) for r in rows],
    }


def delete_case(case_id: str) -> bool:
    with get_db() as conn:
        cur = conn.execute('DELETE FROM cases WHERE id=?', (case_id,))
    return cur.rowcount > 0


# ---------------------------------------------------------------------------
# CRUD — Comments
# ---------------------------------------------------------------------------

def add_comment(case_id: str, content: str) -> dict:
    now = _now()
    with get_db() as conn:
        # Ensure case exists
        if not conn.execute('SELECT 1 FROM cases WHERE id=?', (case_id,)).fetchone():
            raise ValueError(f'Case {case_id} not found')
        conn.execute(
            'INSERT INTO comments (case_id, created_at, content) VALUES (?,?,?)',
            (case_id, now, content),
        )
        row = conn.execute(
            'SELECT * FROM comments WHERE case_id=? ORDER BY id DESC LIMIT 1',
            (case_id,),
        ).fetchone()
    return dict(row)


def list_comments(case_id: str) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            'SELECT * FROM comments WHERE case_id=? ORDER BY created_at ASC',
            (case_id,),
        ).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# CRUD — Corrections
# ---------------------------------------------------------------------------

VALID_LABELS = [
    'no-tumor', 'osteochondroma', 'multiple osteochondromas',
    'simple bone cyst', 'giant cell tumor', 'osteofibroma',
    'synovial osteochondroma', 'other bt', 'osteosarcoma', 'other mt',
]


def add_correction(case_id: str, corrected_label: str, reason: str = '') -> dict:
    if corrected_label not in VALID_LABELS:
        raise ValueError(f'Invalid label: {corrected_label}. Must be one of {VALID_LABELS}')
    now = _now()
    with get_db() as conn:
        if not conn.execute('SELECT 1 FROM cases WHERE id=?', (case_id,)).fetchone():
            raise ValueError(f'Case {case_id} not found')
        conn.execute(
            'INSERT INTO corrections (case_id, created_at, corrected_label, reason) VALUES (?,?,?,?)',
            (case_id, now, corrected_label, reason),
        )
        row = conn.execute(
            'SELECT * FROM corrections WHERE case_id=? ORDER BY id DESC LIMIT 1',
            (case_id,),
        ).fetchone()
    return dict(row)


def list_corrections(case_id: str) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            'SELECT * FROM corrections WHERE case_id=? ORDER BY created_at ASC',
            (case_id,),
        ).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Dashboard statistics
# ---------------------------------------------------------------------------

def get_stats() -> dict:
    with get_db() as conn:
        total = conn.execute('SELECT COUNT(*) FROM cases').fetchone()[0]

        # Cases per label
        label_rows = conn.execute(
            'SELECT top1_label, COUNT(*) as cnt FROM cases GROUP BY top1_label ORDER BY cnt DESC'
        ).fetchall()
        labels_dist = {r['top1_label']: r['cnt'] for r in label_rows}

        # Recent 7 days activity
        daily_rows = conn.execute(
            """SELECT DATE(created_at) as day, COUNT(*) as cnt
               FROM cases
               WHERE created_at >= DATE('now', '-7 days')
               GROUP BY day ORDER BY day"""
        ).fetchall()
        daily = {r['day']: r['cnt'] for r in daily_rows}

        # Cases with corrections
        corrected = conn.execute(
            'SELECT COUNT(DISTINCT case_id) FROM corrections'
        ).fetchone()[0]

        # Cases with comments
        commented = conn.execute(
            'SELECT COUNT(DISTINCT case_id) FROM comments'
        ).fetchone()[0]

        # Device distribution
        device_rows = conn.execute(
            'SELECT device, COUNT(*) as cnt FROM cases GROUP BY device'
        ).fetchall()
        devices = {r['device']: r['cnt'] for r in device_rows}

        # Average prediction time
        avg_time = conn.execute(
            'SELECT AVG(prediction_seconds) FROM cases'
        ).fetchone()[0]

    return {
        'total_cases': total,
        'labels_distribution': labels_dist,
        'daily_activity': daily,
        'corrected_cases': corrected,
        'commented_cases': commented,
        'device_distribution': devices,
        'avg_prediction_seconds': round(avg_time, 4) if avg_time else 0,
    }
