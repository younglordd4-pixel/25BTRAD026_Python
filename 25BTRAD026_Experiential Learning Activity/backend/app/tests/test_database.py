from __future__ import annotations

from sqlalchemy import create_engine, text as sqltext

from app import database


def test_init_db_preserves_existing_fts_entries(tmp_path, monkeypatch):
    test_engine = create_engine(f"sqlite:///{tmp_path / 'restart.db'}")
    monkeypatch.setattr(database, "engine", test_engine)

    database.init_db()
    with test_engine.begin() as conn:
        conn.execute(
            sqltext(
                "INSERT INTO chunk_fts (chunk_id, document_id, page_number, text) "
                "VALUES (1, 7, 3, 'persistent keyword phrase')"
            )
        )

    database.init_db()

    with test_engine.connect() as conn:
        rows = conn.execute(
            sqltext("SELECT chunk_id FROM chunk_fts WHERE text MATCH 'persistent'")
        ).all()
    assert rows == [(1,)]
    test_engine.dispose()
