"""
tests/test_document_extractor.py — Unit tests for Word & PPT extraction
"""
import zipfile
from io import BytesIO
from pathlib import Path
import pytest

from document_extractor import (
    extract_document,
    extract_docx,
    extract_pptx,
    get_document_type,
    is_supported_document,
)


def test_supported_document_extensions():
    assert is_supported_document("notes.pdf")
    assert is_supported_document("paper.docx")
    assert is_supported_document("presentation.pptx")
    assert is_supported_document("legacy.doc")
    assert is_supported_document("legacy.ppt")
    assert not is_supported_document("image.png")
    assert not is_supported_document("archive.zip")


def test_get_document_type():
    assert get_document_type("test.PDF") == "pdf"
    assert get_document_type("test.docx") == "docx"
    assert get_document_type("test.PPTX") == "pptx"


def test_extract_docx_paragraphs_and_pages(tmp_path):
    docx_file = tmp_path / "sample.docx"
    with zipfile.ZipFile(docx_file, "w") as zf:
        zf.writestr(
            "word/document.xml",
            """<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>Permutations and combinations formula details.</w:t></w:r></w:p>
    <w:p><w:r><w:br w:type="page"/><w:t>Second page content on probability distribution.</w:t></w:r></w:p>
  </w:body>
</w:document>""",
        )

    count, pages, err = extract_docx(docx_file)
    assert err is None
    assert count == 2
    assert "Permutations" in pages[0][1]
    assert "probability" in pages[1][1]


def test_extract_pptx_slides(tmp_path):
    pptx_file = tmp_path / "lecture.pptx"
    with zipfile.ZipFile(pptx_file, "w") as zf:
        zf.writestr(
            "ppt/slides/slide1.xml",
            """<?xml version="1.0" encoding="UTF-8"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld><p:spTree><p:sp><p:txBody>
    <a:p><a:r><a:t>Slide 1: Intro to Physics</a:t></a:r></a:p>
  </p:txBody></p:sp></p:spTree></p:cSld>
</p:sld>""",
        )
        zf.writestr(
            "ppt/slides/slide2.xml",
            """<?xml version="1.0" encoding="UTF-8"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld><p:spTree><p:sp><p:txBody>
    <a:p><a:r><a:t>Slide 2: Newton Second Law F = ma</a:t></a:r></a:p>
  </p:txBody></p:sp></p:spTree></p:cSld>
</p:sld>""",
        )

    count, slides, err = extract_pptx(pptx_file)
    assert err is None
    assert count == 2
    assert "Intro to Physics" in slides[0][1]
    assert "F = ma" in slides[1][1]


def test_extract_corrupted_docx(tmp_path):
    corrupt = tmp_path / "broken.docx"
    corrupt.write_bytes(b"not a valid zip file")
    count, pages, err = extract_document(corrupt)
    # Falls back gracefully without crash
    assert isinstance(count, int)
    assert isinstance(pages, list)

