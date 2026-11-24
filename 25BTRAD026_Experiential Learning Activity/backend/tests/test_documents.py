from __future__ import annotations

import io
from pathlib import Path

import fitz
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.routers import documents
from app.services.search_service import ensure_fts_table


@pytest.fixture()
def client(tmp_path: Path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    with session_factory() as session:
        ensure_fts_table(session)

    def override_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    original_upload_dir = documents.UPLOAD_DIR
    documents.UPLOAD_DIR = tmp_path / "uploads"
    documents.UPLOAD_DIR.mkdir()
    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    documents.UPLOAD_DIR = original_upload_dir


def pdf_bytes(text: str = "Permutation is an arrangement where order matters.") -> bytes:
    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((72, 72), text)
    data = pdf.tobytes()
    pdf.close()
    return data


def test_health(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_upload_extract_list_details_and_pages(client: TestClient):
    response = client.post("/documents/upload", files={"files": ("notes.pdf", io.BytesIO(pdf_bytes()), "application/pdf")})
    assert response.status_code == 201
    document = response.json()[0]
    assert document["filename"] == "notes.pdf"
    assert document["has_extractable_text"] is True
    assert document["extraction_status"] == "completed"

    listing = client.get("/documents")
    assert listing.status_code == 200
    assert len(listing.json()) == 1

    detail = client.get(f"/documents/{document['id']}")
    assert detail.status_code == 200
    assert detail.json()["page_count"] == 1

    pages = client.get(f"/documents/{document['id']}/pages")
    assert pages.status_code == 200
    assert "Permutation" in pages.json()[0]["text"]


def test_scanned_like_pdf_returns_warning(client: TestClient):
    pdf = fitz.open()
    pdf.new_page()
    data = pdf.tobytes()
    pdf.close()
    response = client.post("/documents/upload", files={"files": ("scan.pdf", io.BytesIO(data), "application/pdf")})
    assert response.status_code == 201
    assert response.json()[0]["extraction_status"] == "warning"
    assert response.json()[0]["has_extractable_text"] is False


def test_non_pdf_is_rejected(client: TestClient):
    response = client.post("/documents/upload", files={"files": ("notes.txt", io.BytesIO(b"not pdf"), "text/plain")})
    assert response.status_code == 400
    assert "supported PDF" in response.json()["detail"]


def test_delete_removes_document(client: TestClient):
    uploaded = client.post("/documents/upload", files={"files": ("delete-me.pdf", io.BytesIO(pdf_bytes()), "application/pdf")}).json()[0]
    response = client.delete(f"/documents/{uploaded['id']}")
    assert response.status_code == 200
    assert client.get(f"/documents/{uploaded['id']}").status_code == 404
