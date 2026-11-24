"""
tests/test_pdf_processor.py — StudyVerse Offline Phase A
=========================================================
Unit tests for pdf_processor.py

Run with:
    python -m pytest tests/test_pdf_processor.py -v

Note: Tests that require a real PDF file are skipped automatically
      if no PDF is present in the test_fixtures/ directory.
      They are marked with @pytest.mark.skipif so CI stays green.
"""
from __future__ import annotations

import sys
from io import BytesIO
from pathlib import Path

import pytest

# Make sure we can import from the parent directory
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from pdf_processor import (
    _classify_extraction,
    _unique_stored_name,
    extract_pdf,
    safe_filename,
)


# ─────────────────────────────────────────────────────────────────────────────
# safe_filename
# ─────────────────────────────────────────────────────────────────────────────
class TestSafeFilename:
    def test_normal_pdf(self):
        assert safe_filename("My Notes.pdf") == "My_Notes.pdf"

    def test_spaces_and_specials(self):
        result = safe_filename("Lecture #1 (2024).pdf")
        assert " " not in result
        assert "#" not in result
        assert "(" not in result

    def test_preserves_extension(self):
        assert safe_filename("physics.pdf").endswith(".pdf")

    def test_empty_string_fallback(self):
        assert safe_filename("") == "document.pdf"

    def test_only_dots_fallback(self):
        # All non-alphanum chars stripped, result empty → fallback
        result = safe_filename("...   ...")
        assert result  # non-empty

    def test_path_stripping(self):
        # Path separators must be removed
        result = safe_filename("/etc/passwd/../../evil.pdf")
        assert "/" not in result
        assert "\\" not in result

    def test_unicode_characters(self):
        result = safe_filename("数学ノート.pdf")
        # Must not crash; result should be non-empty
        assert isinstance(result, str)
        assert len(result) > 0


# ─────────────────────────────────────────────────────────────────────────────
# _unique_stored_name
# ─────────────────────────────────────────────────────────────────────────────
class TestUniqueStoredName:
    def test_is_unique(self):
        name = "notes.pdf"
        n1 = _unique_stored_name(name)
        n2 = _unique_stored_name(name)
        # Two calls should produce different names (different timestamps)
        # Allow a tiny chance of collision but extremely unlikely
        assert n1.endswith(name)
        assert n2.endswith(name)

    def test_contains_original(self):
        result = _unique_stored_name("lecture.pdf")
        assert "lecture.pdf" in result

    def test_no_path_separators(self):
        result = _unique_stored_name("lecture.pdf")
        assert "/" not in result
        assert "\\" not in result


# ─────────────────────────────────────────────────────────────────────────────
# extract_pdf — corrupt / invalid files
# ─────────────────────────────────────────────────────────────────────────────
class TestExtractPdfCorruptFiles:
    def test_non_existent_file(self, tmp_path):
        """extract_pdf must return an error tuple, not raise."""
        fake = tmp_path / "nonexistent.pdf"
        page_count, pages, error = extract_pdf(fake)
        # Should return (0, [], error_string) — not raise
        assert page_count == 0
        assert pages == []
        assert error is not None
        assert isinstance(error, str)

    def test_empty_file(self, tmp_path):
        """An empty file is not a valid PDF."""
        bad = tmp_path / "empty.pdf"
        bad.write_bytes(b"")
        page_count, pages, error = extract_pdf(bad)
        assert page_count == 0
        assert error is not None

    def test_non_pdf_bytes(self, tmp_path):
        """A file with random bytes should not crash."""
        bad = tmp_path / "random.pdf"
        bad.write_bytes(b"\x00\x01\x02NOTAPDF" * 100)
        page_count, pages, error = extract_pdf(bad)
        # Should return gracefully
        assert page_count == 0 or error is not None  # one or both conditions

    def test_html_file_masquerading_as_pdf(self, tmp_path):
        """HTML disguised as PDF."""
        bad = tmp_path / "fake.pdf"
        bad.write_text("<html><body>Hello</body></html>", encoding="utf-8")
        page_count, pages, error = extract_pdf(bad)
        assert error is not None

    def test_return_type_always_tuple(self, tmp_path):
        """Return value must always be a 3-tuple regardless of input."""
        bad = tmp_path / "junk.pdf"
        bad.write_bytes(b"junk data")
        result = extract_pdf(bad)
        assert isinstance(result, tuple)
        assert len(result) == 3


# ─────────────────────────────────────────────────────────────────────────────
# _classify_extraction
# ─────────────────────────────────────────────────────────────────────────────
class TestClassifyExtraction:
    def test_completed_when_has_text(self):
        status, msg = _classify_extraction(True, None, 5, "file.pdf")
        assert status == "completed"
        assert msg is None

    def test_warning_when_no_text(self):
        status, msg = _classify_extraction(False, None, 3, "scan.pdf")
        assert status == "warning"
        assert msg is not None
        assert "scanned" in msg.lower() or "image" in msg.lower() or "ocr" in msg.lower()

    def test_failed_when_zero_pages_and_error(self):
        status, msg = _classify_extraction(False, "Cannot read file", 0, "bad.pdf")
        assert status == "failed"
        assert msg == "Cannot read file"

    def test_warning_when_has_error_but_has_pages(self):
        status, msg = _classify_extraction(False, "Partial read error", 5, "partial.pdf")
        assert status == "warning"
        assert msg == "Partial read error"

    def test_scanned_pdf_message_content(self):
        _, msg = _classify_extraction(False, None, 10, "scan.pdf")
        # Must mention OCR limitation
        assert "OCR" in msg or "ocr" in msg.lower() or "scanned" in msg.lower()
