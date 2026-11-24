"""
test_docx_pptx_api.py — Verify uploading and processing Word and PowerPoint documents
"""
import io
import zipfile
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def make_test_docx(text_page_1: str, text_page_2: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(
            "word/document.xml",
            f"""<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>{text_page_1}</w:t></w:r></w:p>
    <w:p><w:r><w:br w:type="page"/><w:t>{text_page_2}</w:t></w:r></w:p>
  </w:body>
</w:document>""",
        )
    return buf.getvalue()


def make_test_pptx(slide1_text: str, slide2_text: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(
            "ppt/slides/slide1.xml",
            f"""<?xml version="1.0" encoding="UTF-8"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld><p:spTree><p:sp><p:txBody>
    <a:p><a:r><a:t>{slide1_text}</a:t></a:r></a:p>
  </p:txBody></p:sp></p:spTree></p:cSld>
</p:sld>""",
        )
        zf.writestr(
            "ppt/slides/slide2.xml",
            f"""<?xml version="1.0" encoding="UTF-8"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld><p:spTree><p:sp><p:txBody>
    <a:p><a:r><a:t>{slide2_text}</a:t></a:r></a:p>
  </p:txBody></p:sp></p:spTree></p:cSld>
</p:sld>""",
        )
    return buf.getvalue()


def test_upload_and_extract_docx(client: TestClient):
    docx_bytes = make_test_docx(
        "Permutations and arrangements where order matters in mathematics.",
        "Newton second law states that Force equals mass times acceleration F = ma.",
    )
    files = {"files": ("lecture_notes.docx", io.BytesIO(docx_bytes), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    res = client.post("/documents/upload", files=files)
    assert res.status_code == 201, res.text
    data = res.json()
    assert len(data) == 1
    doc = data[0]
    assert doc["filename"] == "lecture_notes.docx"
    assert doc["page_count"] == 2
    assert doc["extraction_status"] == "completed"

    # Verify pages
    pages_res = client.get(f"/documents/{doc['id']}/pages")
    assert pages_res.status_code == 200
    pages = pages_res.json()
    assert len(pages) == 2
    assert "Permutations" in pages[0]["text"]
    assert "Newton" in pages[1]["text"]

    # Delete cleanup
    del_res = client.delete(f"/documents/{doc['id']}")
    assert del_res.status_code == 200


def test_upload_and_extract_pptx(client: TestClient):
    pptx_bytes = make_test_pptx(
        "Introduction to Deep Learning and Gradient Descent",
        "Backpropagation Algorithm and Neural Network Weights",
    )
    files = {"files": ("ai_lecture.pptx", io.BytesIO(pptx_bytes), "application/vnd.openxmlformats-officedocument.presentationml.presentation")}
    res = client.post("/documents/upload", files=files)
    assert res.status_code == 201, res.text
    data = res.json()
    assert len(data) == 1
    doc = data[0]
    assert doc["filename"] == "ai_lecture.pptx"
    assert doc["page_count"] == 2
    assert doc["extraction_status"] == "completed"

    # Verify slides
    pages_res = client.get(f"/documents/{doc['id']}/pages")
    assert pages_res.status_code == 200
    pages = pages_res.json()
    assert len(pages) == 2
    assert "Deep Learning" in pages[0]["text"]
    assert "Backpropagation" in pages[1]["text"]

    # Delete cleanup
    del_res = client.delete(f"/documents/{doc['id']}")
    assert del_res.status_code == 200
