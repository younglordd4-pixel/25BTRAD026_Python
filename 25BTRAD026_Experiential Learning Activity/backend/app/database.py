from __future__ import annotations

import os
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


BACKEND_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.getenv("STUDYVERSE_DATA_DIR", BACKEND_DIR / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
INDEX_DIR = DATA_DIR / "indexes"
INDEX_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_URL = os.getenv("STUDYVERSE_DATABASE_URL", f"sqlite:///{DATA_DIR / 'studyverse.db'}")


class Base(DeclarativeBase):
    pass


connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)


def init_db() -> None:
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)

    # Small additive migration for databases created before deletion tracking.
    with engine.begin() as conn:
        columns = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(documents)")}
        if "deletion_status" not in columns:
            conn.exec_driver_sql("ALTER TABLE documents ADD COLUMN deletion_status VARCHAR(32)")
        if "deletion_error" not in columns:
            conn.exec_driver_sql("ALTER TABLE documents ADD COLUMN deletion_error TEXT")
    
    # Create the FTS5 table only when absent; startup must preserve its entries.
    with engine.connect() as conn:
        from sqlalchemy import text as sqltext
        conn.execute(sqltext("""
            CREATE VIRTUAL TABLE IF NOT EXISTS chunk_fts USING fts5(
                chunk_id UNINDEXED,
                document_id UNINDEXED,
                page_number UNINDEXED,
                text
            )
        """))
        conn.commit()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
