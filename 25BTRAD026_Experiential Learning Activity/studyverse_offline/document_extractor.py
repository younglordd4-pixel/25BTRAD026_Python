"""
document_extractor.py — Unified Text Extraction for PDF, DOCX, and PPTX
========================================================================
Extracts page-wise (or slide-wise) text from:
  • PDF (.pdf)
  • Microsoft Word (.docx, .doc)
  • Microsoft PowerPoint (.pptx, .ppt)

Zero mandatory external dependencies beyond standard library for DOCX/PPTX.
Uses PyMuPDF for PDF when available.
"""
from __future__ import annotations

import io
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import IO


# Namespaces for OpenXML
DOCX_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
PPTX_A_NS = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
PPTX_P_NS = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main"}


def get_document_type(filename_or_path: str | Path) -> str:
    """Return lowercase normalized extension without dot, e.g. 'pdf', 'docx', 'pptx'."""
    suffix = Path(filename_or_path).suffix.lower().lstrip(".")
    return suffix or "pdf"


def is_supported_document(filename_or_path: str | Path) -> bool:
    """Check if the file format is supported."""
    ext = get_document_type(filename_or_path)
    return ext in {"pdf", "docx", "doc", "pptx", "ppt"}


def extract_docx(path: Path) -> tuple[int, list[tuple[int, str]], str | None]:
    """
    Extract text from a Word (.docx) document.
    Uses section/page breaks and character thresholds to paginate naturally.
    """
    try:
        with zipfile.ZipFile(str(path), "r") as zf:
            if "word/document.xml" not in zf.namelist():
                return 0, [], "Invalid DOCX file: missing word/document.xml."

            xml_data = zf.read("word/document.xml")
            tree = ET.fromstring(xml_data)

            pages: list[str] = []
            cur_page_lines: list[str] = []
            cur_char_count = 0

            # Iterate over paragraphs and tables
            for p in tree.iterfind(".//w:p", DOCX_NS):
                # Check for explicit page break in runs
                has_page_break = False
                for br in p.iterfind(".//w:br", DOCX_NS):
                    if br.get(f"{{{DOCX_NS['w']}}}type") == "page":
                        has_page_break = True
                        break
                if p.find(".//w:lastRenderedPageBreak", DOCX_NS) is not None:
                    has_page_break = True

                # Extract all text in paragraph
                texts = [node.text for node in p.iterfind(".//w:t", DOCX_NS) if node.text]
                p_text = "".join(texts).strip()

                # If page break encountered and we have accumulated content, advance page
                if has_page_break and cur_page_lines:
                    pages.append("\n".join(cur_page_lines).strip())
                    cur_page_lines = []
                    cur_char_count = 0

                if p_text:
                    cur_page_lines.append(p_text)
                    cur_char_count += len(p_text)

                # Paginate long documents if no manual page breaks are set (~2500 chars per page)
                if cur_char_count >= 2500 and cur_page_lines:
                    pages.append("\n".join(cur_page_lines).strip())
                    cur_page_lines = []
                    cur_char_count = 0

            if cur_page_lines:
                pages.append("\n".join(cur_page_lines).strip())

            if not pages:
                # Document has no text
                return 1, [(1, "")], None

            page_tuples = [(i, text) for i, text in enumerate(pages, start=1)]
            return len(page_tuples), page_tuples, None

    except zipfile.BadZipFile:
        # Fallback: might be older .doc binary or corrupted
        return _extract_legacy_binary_text(path, "DOC")
    except Exception as exc:
        return 0, [], f"Could not read Word document: {exc}"


def extract_pptx(path: Path) -> tuple[int, list[tuple[int, str]], str | None]:
    """
    Extract slide-wise text from a PowerPoint (.pptx) presentation.
    Each slide corresponds to 1 page.
    """
    try:
        with zipfile.ZipFile(str(path), "r") as zf:
            # Find all slide xml files
            slide_entries = [
                name for name in zf.namelist()
                if re.match(r"^ppt/slides/slide\d+\.xml$", name)
            ]

            if not slide_entries:
                return 0, [], "Invalid PPTX file: no slides found in presentation."

            # Sort slides in numerical order: slide1.xml, slide2.xml, ...
            def slide_num(name: str) -> int:
                m = re.search(r"slide(\d+)\.xml", name)
                return int(m.group(1)) if m else 0

            slide_entries.sort(key=slide_num)

            pages: list[tuple[int, str]] = []

            for i, slide_path in enumerate(slide_entries, start=1):
                slide_xml = zf.read(slide_path)
                tree = ET.fromstring(slide_xml)

                # Extract all text runs
                texts = [node.text for node in tree.iterfind(".//a:t", PPTX_A_NS) if node.text]
                slide_text = "\n".join(t.strip() for t in texts if t.strip())
                pages.append((i, slide_text))

            return len(pages), pages, None

    except zipfile.BadZipFile:
        return _extract_legacy_binary_text(path, "PPT")
    except Exception as exc:
        return 0, [], f"Could not read PowerPoint presentation: {exc}"


def _extract_legacy_binary_text(path: Path, doc_type: str) -> tuple[int, list[tuple[int, str]], str | None]:
    """
    Best-effort text extraction for legacy binary formats (.doc, .ppt).
    Extracts readable ASCII/Unicode text blocks.
    """
    try:
        data = path.read_bytes()
        pattern = re.compile(rb"[\x20-\x7E\t\r\n]{5,}")
        matches = pattern.findall(data)
        decoded = []
        for m in matches:
            try:
                decoded.append(m.decode("latin1", errors="ignore").strip())
            except Exception:
                pass
        text = "\n".join(d for d in decoded if len(d) > 10)
        if not text:
            return 0, [], f"This {doc_type} file could not be parsed. Please convert it to modern .{doc_type.lower()}x format."
        return 1, [(1, text)], None
    except Exception as exc:
        return 0, [], f"Could not read {doc_type} file: {exc}"


def extract_document(path: Path) -> tuple[int, list[tuple[int, str]], str | None]:
    """
    Unified extraction router based on file extension.
    Returns: (page_count, [(page_number, text), ...], error_message)
    """
    ext = get_document_type(path)

    if ext in ("docx", "doc"):
        return extract_docx(path)
    elif ext in ("pptx", "ppt"):
        return extract_pptx(path)
    else:
        # Default to PDF extraction
        try:
            import fitz
            with fitz.open(str(path)) as pdf:
                if not pdf.is_pdf:
                    return 0, [], "This file could not be opened as a PDF. It may be corrupt."
                if pdf.needs_pass:
                    return 0, [], "This PDF is password-protected and cannot be extracted."
                page_count = len(pdf)
                pages: list[tuple[int, str]] = []
                for i, page in enumerate(pdf, start=1):
                    try:
                        raw = page.get_text("text") or ""
                        pages.append((i, raw.strip()))
                    except Exception:
                        pages.append((i, ""))
                return page_count, pages, None
        except Exception as exc:
            return 0, [], f"PDF extraction failed: {exc}"

