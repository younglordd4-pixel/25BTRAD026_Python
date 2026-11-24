from __future__ import annotations

import io
from pathlib import Path

import fitz
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import Chunk
from app.models import Document, Flashcard, StudyLog
from app.routers import documents
from app.services import embedding_service
from app.services.search_service import ensure_fts_table


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)

    # Create the FTS5 virtual table that init_db() would normally build
    with session_factory() as _init_session:
        ensure_fts_table(_init_session)


    def override_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    original_upload_dir = documents.UPLOAD_DIR
    original_index_dir = embedding_service.INDEX_DIR
    documents.UPLOAD_DIR = tmp_path / "uploads"
    documents.UPLOAD_DIR.mkdir()
    embedding_service.INDEX_DIR = tmp_path / "indexes"
    embedding_service.INDEX_DIR.mkdir()
    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    documents.UPLOAD_DIR = original_upload_dir
    embedding_service.INDEX_DIR = original_index_dir


def pdf_bytes(text: str) -> bytes:
    pdf = fitz.open()
    page = pdf.new_page()
    rect = fitz.Rect(50, 50, 550, 750)
    page.insert_textbox(rect, text)
    data = pdf.tobytes()
    pdf.close()
    return data


def upload_document(client: TestClient, text: str = "A permutation is an arrangement of objects in a particular order. The nPr formula counts arrangements where order matters."):
    response = client.post("/documents/upload", files={"files": ("math.pdf", io.BytesIO(pdf_bytes(text)), "application/pdf")})
    assert response.status_code == 201
    return response.json()[0]


def fake_index_builder(document, chunks, index_path, metadata_path):
    index_path.write_bytes(b"test index")
    metadata_path.write_text("[]", encoding="utf-8")
    return True


def test_search_validation_errors(client: TestClient):
    blank = client.post("/search", json={"query": " ", "mode": "hybrid", "top_k": 5, "min_score": 0})
    assert blank.status_code == 422
    bad_mode = client.post("/search", json={"query": "x", "mode": "bad", "top_k": 5, "min_score": 0})
    assert bad_mode.status_code == 422
    bad_top_k = client.post("/search", json={"query": "x", "mode": "hybrid", "top_k": 11, "min_score": 0})
    assert bad_top_k.status_code == 422
    bad_min = client.post("/search", json={"query": "x", "mode": "hybrid", "top_k": 5, "min_score": 1.5})
    assert bad_min.status_code == 422


def test_search_without_indexed_documents_returns_clear_message(client: TestClient):
    response = client.post("/search", json={"query": "permutation", "mode": "keyword", "top_k": 5, "min_score": 0})
    assert response.status_code == 200
    assert response.json()["results"] == []
    assert "No indexed documents" in response.json()["message"]


def test_indexing_replaces_chunks_and_keyword_search_finds_formula(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("app.routers.documents.build_document_faiss_index", fake_index_builder)
    document = upload_document(client, " ".join(["The nPr formula is used for permutation arrangements where order matters."] * 40))

    first = client.post(f"/documents/{document['id']}/index")
    second = client.post(f"/documents/{document['id']}/index")
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["chunks_created"] == second.json()["chunks_created"]

    generator = app.dependency_overrides[get_db]()
    db = next(generator)
    try:
        chunks = list(db.scalars(select(Chunk).where(Chunk.document_id == document["id"])).all())
    finally:
        try:
            next(generator)
        except StopIteration:
            pass
    assert len(chunks) == second.json()["chunks_created"]

    response = client.post("/search", json={"query": "nPr", "mode": "keyword", "top_k": 5, "min_score": 0})
    assert response.status_code == 200
    body = response.json()
    assert body["results"]
    assert body["results"][0]["filename"] == "math.pdf"
    assert body["results"][0]["page_number"] == 1
    assert "<script" not in body["results"][0]["snippet"].lower()


def test_malformed_fts_query_does_not_crash(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("app.routers.documents.build_document_faiss_index", fake_index_builder)
    document = upload_document(client, " ".join(["Factorial notation appears in permutation formulas."] * 40))
    assert client.post(f"/documents/{document['id']}/index").status_code == 200
    response = client.post("/search", json={"query": '" nPr * )', "mode": "keyword", "top_k": 5, "min_score": 0})
    assert response.status_code == 200


def test_delete_document_removes_chunks_and_fts_entries(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("app.routers.documents.build_document_faiss_index", fake_index_builder)
    document = upload_document(client, " ".join(["Newton described force and acceleration relationships."] * 40))
    assert client.post(f"/documents/{document['id']}/index").status_code == 200
    deleted = client.delete(f"/documents/{document['id']}")
    assert deleted.status_code == 200
    debug = client.get(f"/search/debug/document/{document['id']}")
    assert debug.status_code == 404


def test_upload_rejects_actual_size_over_limit(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(documents, "MAX_UPLOAD_BYTES", 10)
    response = client.post(
        "/documents/upload",
        files={"files": ("large.pdf", io.BytesIO(b"%PDF-" + b"x" * 20), "application/pdf")},
    )
    assert response.status_code == 413
    assert "upload limit" in response.json()["detail"]


def test_upload_rejects_invalid_pdf_signature(client: TestClient):
    response = client.post(
        "/documents/upload",
        files={"files": ("invalid.pdf", io.BytesIO(b"not a PDF"), "application/pdf")},
    )
    assert response.status_code == 400
    assert "valid PDF" in response.json()["detail"]


def test_upload_rejects_unparseable_pdf_with_pdf_signature(client: TestClient):
    response = client.post(
        "/documents/upload",
        files={"files": ("broken.pdf", io.BytesIO(b"%PDF-1.7\nnot a real PDF"), "application/pdf")},
    )
    assert response.status_code == 400
    assert "readable PDF" in response.json()["detail"]


def test_upload_rejects_page_count_over_limit(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    pdf = fitz.open()
    pdf.new_page()
    pdf.new_page()
    data = pdf.tobytes()
    pdf.close()
    monkeypatch.setattr(documents, "MAX_PDF_PAGES", 1)
    response = client.post("/documents/upload", files={"files": ("many.pdf", io.BytesIO(data), "application/pdf")})
    assert response.status_code == 413
    assert "page limit" in response.json()["detail"]


def test_reindex_failure_preserves_previous_keyword_index(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("app.routers.documents.build_document_faiss_index", fake_index_builder)
    document = upload_document(client, " ".join(["The preserved phrase describes a stable indexed passage."] * 40))
    assert client.post(f"/documents/{document['id']}/index").status_code == 200

    def fail_builder(*args, **kwargs):
        raise RuntimeError("simulated model failure")

    monkeypatch.setattr("app.routers.documents.build_document_faiss_index", fail_builder)
    failed = client.post(f"/documents/{document['id']}/index")
    assert failed.status_code == 500
    assert "previous index was retained" in failed.json()["detail"]

    search = client.post("/search", json={"query": "preserved", "mode": "keyword", "top_k": 5})
    assert search.status_code == 200
    assert search.json()["results"]


def test_successful_delete_removes_flashcards_review_logs_and_index_files(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("app.routers.documents.build_document_faiss_index", fake_index_builder)
    document = upload_document(client, " ".join(["Newton described force and acceleration relationships."] * 40))
    assert client.post(f"/documents/{document['id']}/index").status_code == 200

    generator = app.dependency_overrides[get_db]()
    db = next(generator)
    card = Flashcard(document_id=document["id"], question="Q", answer="A", context="", page_number=1)
    db.add(card)
    db.commit()
    db.refresh(card)
    db.add(StudyLog(activity_type="revision", card_id=card.id, quality=4, score=0.8))
    db.commit()
    next(generator, None)

    response = client.delete(f"/documents/{document['id']}")
    assert response.status_code == 200
    assert response.json()["cleanup_complete"] is True
    assert client.get(f"/documents/{document['id']}").status_code == 404
    generator = app.dependency_overrides[get_db]()
    db = next(generator)
    assert db.scalar(select(Flashcard.id).where(Flashcard.document_id == document["id"])) is None
    assert db.scalar(select(StudyLog.id).where(StudyLog.card_id == card.id)) is None
    assert not list(documents.UPLOAD_DIR.glob("*"))
    assert not list(embedding_service.INDEX_DIR.glob(f"document_{document['id']}.*"))
    next(generator, None)


def test_partial_delete_retains_document_and_records_cleanup_error(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    document = upload_document(client)
    upload_path = documents.UPLOAD_DIR / next(
        path.name for path in documents.UPLOAD_DIR.glob("*") if path.is_file()
    )
    original_unlink = type(upload_path).unlink

    def fail_uploaded_file_unlink(path, *args, **kwargs):
        if path == upload_path:
            raise PermissionError("simulated file lock")
        return original_unlink(path, *args, **kwargs)

    monkeypatch.setattr(type(upload_path), "unlink", fail_uploaded_file_unlink)
    response = client.delete(f"/documents/{document['id']}")
    assert response.status_code == 200
    body = response.json()
    assert body["cleanup_complete"] is False
    assert body["cleanup_errors"]

    generator = app.dependency_overrides[get_db]()
    db = next(generator)
    retained = db.get(Document, document["id"])
    assert retained is not None
    assert retained.deletion_status == "partial"
    assert retained.deletion_error
    next(generator, None)
