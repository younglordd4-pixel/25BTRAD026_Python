"""
database.py — StudyVerse Offline
=================================
Plain sqlite3 database layer.  No SQLAlchemy, no FastAPI, no external ORM.

Tables
------
documents   — one row per uploaded PDF
page_text   — one row per (document, page)
chunks      — one row per text chunk (used for search)
chunk_fts   — FTS5 virtual table (keyword search); created only if FTS5 is available

All functions receive/return plain Python dicts so the rest of the codebase
does not need to know anything about sqlite3 cursors.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
_HERE = Path(__file__).resolve().parent
DATA_DIR   = _HERE / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
INDEX_DIR  = DATA_DIR / "indexes"
DB_PATH    = DATA_DIR / "studyverse.db"

DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
INDEX_DIR.mkdir(parents=True, exist_ok=True)


# ── Helpers ────────────────────────────────────────────────────────────────────
def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_connection() -> sqlite3.Connection:
    """Open (or create) the SQLite database and return a connection."""
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row          # rows accessible by column name
    conn.execute("PRAGMA journal_mode=WAL")  # better concurrency
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# ── FTS5 capability detection ──────────────────────────────────────────────────
def _fts5_available(conn: sqlite3.Connection) -> bool:
    """Return True if the local SQLite build includes FTS5."""
    try:
        conn.execute(
            "CREATE VIRTUAL TABLE IF NOT EXISTS _fts5_probe USING fts5(x)"
        )
        conn.execute("DROP TABLE IF EXISTS _fts5_probe")
        conn.commit()
        return True
    except sqlite3.OperationalError:
        return False


# ── Schema creation ────────────────────────────────────────────────────────────
_CREATE_DOCUMENTS = """
CREATE TABLE IF NOT EXISTS documents (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    filename            TEXT    NOT NULL,
    stored_filename     TEXT    NOT NULL UNIQUE,
    page_count          INTEGER NOT NULL DEFAULT 0,
    extracted_page_count INTEGER NOT NULL DEFAULT 0,
    has_extractable_text INTEGER NOT NULL DEFAULT 0,  -- boolean (0/1)
    extraction_status   TEXT    NOT NULL DEFAULT 'pending',
    extraction_message  TEXT,
    uploaded_at         TEXT    NOT NULL
)
"""

_CREATE_PAGE_TEXT = """
CREATE TABLE IF NOT EXISTS page_text (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id     INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    page_number     INTEGER NOT NULL,
    text            TEXT    NOT NULL DEFAULT '',
    character_count INTEGER NOT NULL DEFAULT 0
)
"""

_CREATE_CHUNKS = """
CREATE TABLE IF NOT EXISTS chunks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id     INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    page_number     INTEGER NOT NULL,
    chunk_number    INTEGER NOT NULL,
    text            TEXT    NOT NULL,
    character_count INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT    NOT NULL
)
"""

_CREATE_FTS5 = """
CREATE VIRTUAL TABLE IF NOT EXISTS chunk_fts USING fts5(
    chunk_id    UNINDEXED,
    document_id UNINDEXED,
    page_number UNINDEXED,
    text
)
"""

_CREATE_QUIZ_ATTEMPTS = """
CREATE TABLE IF NOT EXISTS quiz_attempts (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    topic               TEXT    NOT NULL,
    document_id         INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    source_filename     TEXT    NOT NULL,
    page_number         INTEGER NOT NULL,
    score               INTEGER NOT NULL,
    total_questions     INTEGER NOT NULL,
    score_percent       REAL    NOT NULL,
    attempted_at        TEXT    NOT NULL
)
"""

_CREATE_REVISION_TOPICS = """
CREATE TABLE IF NOT EXISTS revision_topics (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    topic               TEXT    NOT NULL,
    document_id         INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    source_filename     TEXT    NOT NULL,
    page_number         INTEGER NOT NULL,
    status              TEXT    NOT NULL DEFAULT 'need_revision',
    latest_quiz_score   INTEGER DEFAULT NULL,
    latest_quiz_total   INTEGER DEFAULT NULL,
    last_studied_at     TEXT    NOT NULL,
    next_review_date    TEXT    NOT NULL,
    repetitions         INTEGER NOT NULL DEFAULT 0,
    interval_days       INTEGER NOT NULL DEFAULT 1,
    created_at          TEXT    NOT NULL,
    updated_at          TEXT    NOT NULL,
    UNIQUE(topic, document_id, page_number)
)
"""

_CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_page_text_doc ON page_text(document_id)",
    "CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(document_id)",
    "CREATE INDEX IF NOT EXISTS idx_chunks_page ON chunks(document_id, page_number)",
    "CREATE INDEX IF NOT EXISTS idx_quiz_attempts_topic ON quiz_attempts(topic)",
    "CREATE INDEX IF NOT EXISTS idx_revision_topics_date ON revision_topics(next_review_date)",
]


def init_db() -> bool:
    """
    Initialise database schema.

    Returns True if FTS5 is available and was created, False if the fallback
    (in-memory keyword frequency search) will be used instead.
    """
    conn = get_connection()
    with conn:
        conn.execute(_CREATE_DOCUMENTS)
        conn.execute(_CREATE_PAGE_TEXT)
        conn.execute(_CREATE_CHUNKS)
        conn.execute(_CREATE_QUIZ_ATTEMPTS)
        conn.execute(_CREATE_REVISION_TOPICS)
        for idx_sql in _CREATE_INDEXES:
            conn.execute(idx_sql)

        fts5_ok = _fts5_available(conn)
        if fts5_ok:
            conn.execute(_CREATE_FTS5)

    conn.close()
    return fts5_ok


# ── Document CRUD ──────────────────────────────────────────────────────────────
def insert_document(
    conn: sqlite3.Connection,
    *,
    filename: str,
    stored_filename: str,
    page_count: int,
    extracted_page_count: int,
    has_extractable_text: bool,
    extraction_status: str,
    extraction_message: str | None,
) -> int:
    """Insert a document record and return its new id."""
    cur = conn.execute(
        """
        INSERT INTO documents
            (filename, stored_filename, page_count, extracted_page_count,
             has_extractable_text, extraction_status, extraction_message, uploaded_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            filename,
            stored_filename,
            page_count,
            extracted_page_count,
            1 if has_extractable_text else 0,
            extraction_status,
            extraction_message,
            _utc_now(),
        ),
    )
    conn.commit()
    return cur.lastrowid  # type: ignore[return-value]


def get_document(conn: sqlite3.Connection, doc_id: int) -> dict | None:
    """Return one document as a dict, or None if not found."""
    row = conn.execute(
        "SELECT * FROM documents WHERE id = ?", (doc_id,)
    ).fetchone()
    return dict(row) if row else None


def list_documents(conn: sqlite3.Connection) -> list[dict]:
    """Return all documents ordered by upload time (newest first)."""
    rows = conn.execute(
        "SELECT * FROM documents ORDER BY uploaded_at DESC"
    ).fetchall()
    return [dict(r) for r in rows]


def delete_document(conn: sqlite3.Connection, doc_id: int) -> None:
    """Delete a document and cascade to page_text and chunks."""
    conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    conn.commit()


def get_document_chunk_count(conn: sqlite3.Connection, doc_id: int) -> int:
    row = conn.execute(
        "SELECT COUNT(*) FROM chunks WHERE document_id = ?", (doc_id,)
    ).fetchone()
    return row[0] if row else 0


# ── Page text CRUD ─────────────────────────────────────────────────────────────
def insert_page_texts(
    conn: sqlite3.Connection,
    doc_id: int,
    pages: list[tuple[int, str]],
) -> None:
    """Bulk insert (page_number, text) tuples for a document."""
    conn.executemany(
        """
        INSERT INTO page_text (document_id, page_number, text, character_count)
        VALUES (?, ?, ?, ?)
        """,
        [(doc_id, pn, text, len(text)) for pn, text in pages],
    )
    conn.commit()


def get_page_texts(conn: sqlite3.Connection, doc_id: int) -> list[dict]:
    """Return all page rows for a document, ordered by page number."""
    rows = conn.execute(
        "SELECT * FROM page_text WHERE document_id = ? ORDER BY page_number",
        (doc_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def get_page_text(conn: sqlite3.Connection, doc_id: int, page_number: int) -> str:
    """Return the extracted text for a single page (empty string if missing)."""
    row = conn.execute(
        "SELECT text FROM page_text WHERE document_id = ? AND page_number = ?",
        (doc_id, page_number),
    ).fetchone()
    return row["text"] if row else ""


# ── Chunk CRUD ─────────────────────────────────────────────────────────────────
def delete_chunks_for_document(conn: sqlite3.Connection, doc_id: int) -> None:
    """Remove all chunks (and FTS5 entries) for a document before re-indexing."""
    # Delete FTS5 entries (ignore silently if table doesn't exist)
    try:
        conn.execute(
            "DELETE FROM chunk_fts WHERE document_id = ?", (doc_id,)
        )
    except sqlite3.OperationalError:
        pass
    conn.execute("DELETE FROM chunks WHERE document_id = ?", (doc_id,))
    conn.commit()


def insert_chunks(
    conn: sqlite3.Connection,
    chunks: list[dict],
) -> list[int]:
    """
    Bulk insert chunk dicts and return their new IDs.

    Expected keys per chunk dict:
        document_id, page_number, chunk_number, text, character_count
    """
    now = _utc_now()
    ids: list[int] = []
    for c in chunks:
        cur = conn.execute(
            """
            INSERT INTO chunks
                (document_id, page_number, chunk_number, text, character_count, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                c["document_id"],
                c["page_number"],
                c["chunk_number"],
                c["text"],
                c["character_count"],
                now,
            ),
        )
        ids.append(cur.lastrowid)  # type: ignore[arg-type]
    conn.commit()
    return ids


def insert_fts5_entries(
    conn: sqlite3.Connection,
    chunk_rows: list[dict],  # dicts with id, document_id, page_number, text
) -> None:
    """Insert chunk rows into the FTS5 virtual table (if it exists)."""
    try:
        conn.executemany(
            "INSERT INTO chunk_fts (chunk_id, document_id, page_number, text) VALUES (?, ?, ?, ?)",
            [(r["id"], r["document_id"], r["page_number"], r["text"]) for r in chunk_rows],
        )
        conn.commit()
    except sqlite3.OperationalError:
        # FTS5 table not available — keyword fallback will be used
        pass


def get_all_chunks_for_docs(
    conn: sqlite3.Connection,
    doc_ids: list[int] | None = None,
) -> list[dict]:
    """Return all chunks, optionally filtered to a list of document IDs."""
    if doc_ids:
        placeholders = ",".join("?" * len(doc_ids))
        rows = conn.execute(
            f"SELECT c.*, d.filename FROM chunks c JOIN documents d ON c.document_id = d.id WHERE c.document_id IN ({placeholders}) ORDER BY c.document_id, c.page_number, c.chunk_number",
            doc_ids,
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT c.*, d.filename FROM chunks c JOIN documents d ON c.document_id = d.id ORDER BY c.document_id, c.page_number, c.chunk_number"
        ).fetchall()
    return [dict(r) for r in rows]


def get_chunks_by_ids(conn: sqlite3.Connection, chunk_ids: list[int]) -> dict[int, dict]:
    """Return a mapping of chunk_id → chunk dict for the given IDs."""
    if not chunk_ids:
        return {}
    placeholders = ",".join("?" * len(chunk_ids))
    rows = conn.execute(
        f"SELECT c.*, d.filename FROM chunks c JOIN documents d ON c.document_id = d.id WHERE c.id IN ({placeholders})",
        chunk_ids,
    ).fetchall()
    return {r["id"]: dict(r) for r in rows}


# ── Quiz Attempt CRUD ─────────────────────────────────────────────────────────
def insert_quiz_attempt(
    conn: sqlite3.Connection,
    *,
    topic: str,
    document_id: int | None,
    source_filename: str,
    page_number: int,
    score: int,
    total_questions: int,
) -> int:
    """Insert a quiz attempt record and return its new id."""
    pct = round((score / total_questions * 100.0), 1) if total_questions > 0 else 0.0
    now = _utc_now()
    cur = conn.execute(
        """
        INSERT INTO quiz_attempts
            (topic, document_id, source_filename, page_number, score, total_questions, score_percent, attempted_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (topic, document_id, source_filename, page_number, score, total_questions, pct, now),
    )
    conn.commit()
    return cur.lastrowid  # type: ignore[return-value]


def list_quiz_attempts(conn: sqlite3.Connection, limit: int = 5) -> list[dict]:
    """Return recent quiz attempts ordered by attempt time (newest first)."""
    rows = conn.execute(
        "SELECT * FROM quiz_attempts ORDER BY attempted_at DESC LIMIT ?", (limit,)
    ).fetchall()
    return [dict(r) for r in rows]


# ── Revision Topic CRUD ───────────────────────────────────────────────────────
def upsert_revision_topic(
    conn: sqlite3.Connection,
    *,
    topic: str,
    document_id: int | None,
    source_filename: str,
    page_number: int,
    status: str,
    latest_quiz_score: int | None = None,
    latest_quiz_total: int | None = None,
    next_review_date: str,
    repetitions: int = 0,
    interval_days: int = 1,
) -> int:
    """
    Insert or update a tracked revision topic.
    Identified uniquely by (topic, document_id, page_number).
    """
    now = _utc_now()
    # Check if entry exists
    existing = conn.execute(
        """
        SELECT id FROM revision_topics
        WHERE topic = ? AND (document_id = ? OR (document_id IS NULL AND ? IS NULL)) AND page_number = ?
        """,
        (topic, document_id, document_id, page_number),
    ).fetchone()

    if existing:
        conn.execute(
            """
            UPDATE revision_topics
            SET status = ?,
                latest_quiz_score = COALESCE(?, latest_quiz_score),
                latest_quiz_total = COALESCE(?, latest_quiz_total),
                last_studied_at = ?,
                next_review_date = ?,
                repetitions = ?,
                interval_days = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                status,
                latest_quiz_score,
                latest_quiz_total,
                now,
                next_review_date,
                repetitions,
                interval_days,
                now,
                existing["id"],
            ),
        )
        conn.commit()
        return existing["id"]
    else:
        cur = conn.execute(
            """
            INSERT INTO revision_topics
                (topic, document_id, source_filename, page_number, status,
                 latest_quiz_score, latest_quiz_total, last_studied_at, next_review_date,
                 repetitions, interval_days, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                topic,
                document_id,
                source_filename,
                page_number,
                status,
                latest_quiz_score,
                latest_quiz_total,
                now,
                next_review_date,
                repetitions,
                interval_days,
                now,
                now,
            ),
        )
        conn.commit()
        return cur.lastrowid  # type: ignore[return-value]


def list_revision_topics(
    conn: sqlite3.Connection, status_filter: str | None = None
) -> list[dict]:
    """Return all tracked revision topics ordered by next_review_date ASC."""
    if status_filter and status_filter.lower() != "all":
        rows = conn.execute(
            "SELECT * FROM revision_topics WHERE status = ? ORDER BY next_review_date ASC",
            (status_filter.lower(),),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM revision_topics ORDER BY next_review_date ASC"
        ).fetchall()
    return [dict(r) for r in rows]


def get_revision_topic(
    conn: sqlite3.Connection, topic: str, document_id: int | None, page_number: int
) -> dict | None:
    """Return matching revision topic or None if untracked."""
    row = conn.execute(
        """
        SELECT * FROM revision_topics
        WHERE topic = ? AND (document_id = ? OR (document_id IS NULL AND ? IS NULL)) AND page_number = ?
        """,
        (topic, document_id, document_id, page_number),
    ).fetchone()
    return dict(row) if row else None


def delete_revision_topic(conn: sqlite3.Connection, topic_id: int) -> None:
    """Remove a single tracked topic from revision_topics table."""
    conn.execute("DELETE FROM revision_topics WHERE id = ?", (topic_id,))
    conn.commit()


def clear_revision_topics(conn: sqlite3.Connection) -> None:
    """
    Clear all records from revision_topics table ONLY.
    Uploaded PDFs, extracted pages, chunks, and quiz attempts remain intact!
    """
    conn.execute("DELETE FROM revision_topics")
    conn.commit()

