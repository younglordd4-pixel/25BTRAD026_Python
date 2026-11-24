"""
pdf_processor.py — StudyVerse Offline
======================================
PDF ingestion pipeline using PyMuPDF (fitz).

Public API
----------
safe_filename(name)                  → sanitised filename string
save_uploaded_pdf(file_obj, name)    → stored Path + stored_name
extract_pdf(path)                    → (page_count, [(page_num, text)], error | None)
process_and_store_pdf(conn, file_obj, original_name) → result dict

All errors are caught and returned as user-friendly strings.
No raw tracebacks are propagated to the caller.
"""
from __future__ import annotations

import hashlib
import re
from io import BytesIO
from pathlib import Path
from typing import IO

import fitz  # PyMuPDF

from database import (
    UPLOAD_DIR,
    delete_chunks_for_document,
    get_page_texts,
    insert_document,
    insert_page_texts,
)
from document_extractor import extract_document, is_supported_document, get_document_type

import sqlite3


# ── Filename helpers ───────────────────────────────────────────────────────────
def safe_filename(original: str) -> str:
    """
    Return a filesystem-safe version of *original*.
    Replaces any character that is not a letter, digit, dot, underscore, or hyphen
    with an underscore, then strips leading/trailing dots and underscores.
    Falls back to "document.pdf" if the result is empty.
    """
    name = Path(original).name  # strip any path separators
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._")
    return cleaned or "document.pdf"


def _unique_stored_name(original_safe: str) -> str:
    """
    Derive a unique filename by prepending an 8-character hash of the
    original name + current microseconds.  Keeps the original name readable.
    """
    import time
    seed = f"{original_safe}{time.time_ns()}"
    short_hash = hashlib.md5(seed.encode()).hexdigest()[:8]
    return f"{short_hash}_{original_safe}"


# ── File I/O ───────────────────────────────────────────────────────────────────
def save_uploaded_pdf(
    file_obj: IO[bytes] | BytesIO,
    original_name: str,
) -> tuple[Path, str]:
    """
    Write *file_obj* to the uploads directory.
    Supports PDF, Word (.docx, .doc), and PowerPoint (.pptx, .ppt).

    Returns
    -------
    (stored_path, stored_filename)
        stored_path      — absolute Path where the file was saved
        stored_filename  — the unique filename used on disk
    """
    safe = safe_filename(original_name)
    supported_extensions = (".pdf", ".docx", ".doc", ".pptx", ".ppt")
    if not any(safe.lower().endswith(ext) for ext in supported_extensions):
        raise ValueError(f"'{original_name}' is not a supported file type (supported: PDF, Word DOCX/DOC, PowerPoint PPTX/PPT).")

    stored_name = _unique_stored_name(safe)
    target = UPLOAD_DIR / stored_name

    if hasattr(file_obj, "read"):
        data = file_obj.read()
    else:
        data = file_obj

    target.write_bytes(data)
    return target, stored_name


# ── Text extraction ────────────────────────────────────────────────────────────
def extract_pdf(
    path: Path,
) -> tuple[int, list[tuple[int, str]], str | None]:
    """
    Extract page-wise or slide-wise text from a document.
    Supports PDF, Word (.docx, .doc), and PowerPoint (.pptx, .ppt).

    Parameters
    ----------
    path : Path
        Absolute path to the stored document file.

    Returns
    -------
    (page_count, pages, error_message)
        page_count    — total number of pages/slides (0 on failure)
        pages         — list of (1-based page_number, text) tuples
        error_message — None on success, a user-friendly string on failure
    """
    doc_type = get_document_type(path)

    # Route Word and PowerPoint documents to document_extractor
    if doc_type in ("docx", "doc", "pptx", "ppt"):
        return extract_document(path)

    # Standard PDF processing via PyMuPDF
    try:
        with fitz.open(str(path)) as pdf:
            if not pdf.is_pdf:
                return 0, [], (
                    "This file could not be opened as a PDF. "
                    "It may be corrupt or not a valid PDF document."
                )

            # ── Password-protected ──
            if pdf.needs_pass:
                return 0, [], (
                    "This PDF is password-protected and cannot be read locally. "
                    "Please remove the password and re-upload."
                )

            page_count = len(pdf)
            pages: list[tuple[int, str]] = []

            for i, page in enumerate(pdf, start=1):
                try:
                    raw = page.get_text("text") or ""
                    pages.append((i, raw.strip()))
                except Exception:
                    # Individual page failure — record empty text and continue
                    pages.append((i, ""))

            return page_count, pages, None

    except fitz.FileDataError:
        return 0, [], (
            "This file could not be opened as a PDF. "
            "It may be corrupt or not a valid PDF document."
        )
    except RuntimeError as exc:
        return 0, [], (
            f"An error occurred while reading this PDF ({exc.__class__.__name__}). "
            "Please try re-saving or re-exporting the file."
        )
    except Exception as exc:
        # Broad catch: never let a raw traceback reach the UI
        return 0, [], (
            f"An unexpected error occurred: {exc.__class__.__name__}. "
            "Please check that the file is a valid, unencrypted PDF."
        )


def _classify_extraction(
    has_text: bool,
    extraction_error: str | None,
    page_count: int,
    filename: str,
) -> tuple[str, str | None]:
    """
    Map extraction results to a (status, message) pair.

    Status values: 'completed' | 'warning' | 'failed'
    """
    if extraction_error:
        status = "failed" if page_count == 0 else "warning"
        return status, extraction_error

    if not has_text:
        return "warning", (
            "No searchable text was found. "
            "This PDF may be scanned or image-based. "
            "OCR is not included in this version."
        )

    return "completed", None


# ── Full pipeline ──────────────────────────────────────────────────────────────
def process_and_store_pdf(
    conn: sqlite3.Connection,
    file_obj: IO[bytes] | BytesIO,
    original_name: str,
) -> dict:
    """
    Full pipeline: save → extract → store in database.

    Returns a result dict:
        doc_id            int
        filename          str   — original safe filename
        stored_filename   str   — UUID-prefixed filename on disk
        page_count        int
        extracted_pages   int   — pages with non-empty text
        has_text          bool
        extraction_status str   — 'completed' | 'warning' | 'failed'
        extraction_message str | None
        error             str | None  — user-facing error (UI display)
        pages             list[tuple[int,str]]  — (page_num, text) for downstream use
    """
    safe = safe_filename(original_name)

    # ── 1. Save to disk ─────────────────────────────────────────────────────
    try:
        stored_path, stored_name = save_uploaded_pdf(file_obj, original_name)
    except ValueError as exc:
        return {
            "doc_id": None,
            "filename": safe,
            "stored_filename": None,
            "page_count": 0,
            "extracted_pages": 0,
            "has_text": False,
            "extraction_status": "failed",
            "extraction_message": str(exc),
            "error": str(exc),
            "pages": [],
        }

    # ── 2. Extract text ──────────────────────────────────────────────────────
    page_count, pages, extraction_error = extract_pdf(stored_path)
    has_text = any(bool(text) for _, text in pages)
    extracted_pages = sum(1 for _, text in pages if text)
    extraction_status, extraction_message = _classify_extraction(
        has_text, extraction_error, page_count, safe
    )

    # ── 3. Write to database ─────────────────────────────────────────────────
    doc_id = insert_document(
        conn,
        filename=safe,
        stored_filename=stored_name,
        page_count=page_count,
        extracted_page_count=extracted_pages,
        has_extractable_text=has_text,
        extraction_status=extraction_status,
        extraction_message=extraction_message,
    )
    if pages:
        insert_page_texts(conn, doc_id, pages)

    return {
        "doc_id": doc_id,
        "filename": safe,
        "stored_filename": stored_name,
        "page_count": page_count,
        "extracted_pages": extracted_pages,
        "has_text": has_text,
        "extraction_status": extraction_status,
        "extraction_message": extraction_message,
        "error": None,
        "pages": pages,
    }
