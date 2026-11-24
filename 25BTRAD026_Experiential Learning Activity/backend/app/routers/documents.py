from __future__ import annotations

import gc
import re
import os
import shutil
import tempfile
import uuid
from pathlib import Path

import fitz
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import delete, func, select, text as sqltext, update
from sqlalchemy.orm import Session

from ..database import DATA_DIR, get_db
from ..models import Chunk, Document, Flashcard, PageText, StudyLog
from ..schemas import (
    DeleteDocumentResponse,
    DocumentDetailResponse,
    DocumentResponse,
    IndexAllResponse,
    IndexDocumentResponse,
    PageTextResponse,
)
from ..services import embedding_service
from ..services.chunk_service import create_chunk_drafts_for_document, save_chunks
from ..services.document_extractor import (
    extract_document,
    get_document_type,
    is_supported_document,
)
from ..services.embedding_service import build_document_faiss_index, document_index_exists
from ..services.search_service import fts_entry_count, insert_chunk_fts_entries

router = APIRouter(prefix="/documents", tags=["Documents"])
UPLOAD_DIR = DATA_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_UPLOAD_BYTES = int(os.getenv("STUDYVERSE_MAX_UPLOAD_MB", "25")) * 1024 * 1024
MAX_PDF_PAGES = int(os.getenv("STUDYVERSE_MAX_PDF_PAGES", "300"))
UPLOAD_READ_SIZE = 1024 * 1024


def safe_filename(filename: str | None) -> str:
    original = Path(filename or "document.pdf").name
    stem = Path(original).stem
    ext = Path(original).suffix.lower()
    cleaned_stem = re.sub(r"[^A-Za-z0-9._-]+", "_", stem).strip("._") or "document"
    cleaned_ext = re.sub(r"[^A-Za-z0-9.]+", "", ext) or ".pdf"
    return f"{cleaned_stem}{cleaned_ext}"


def extraction_message_for(status_name: str, filename: str) -> str | None:
    if status_name == "warning":
        return f"No searchable text was found in {filename}. It may be scanned or image-based."
    if status_name == "failed":
        return f"{filename} could not be read as a valid document."
    return None


def store_upload(upload: UploadFile) -> tuple[Path, str]:
    filename = safe_filename(upload.filename)
    ext = get_document_type(filename)
    if not is_supported_document(filename):
        raise HTTPException(
            status_code=400,
            detail=f"{filename} is not a supported file format (supported: PDF, Word DOCX/DOC, PowerPoint PPTX/PPT).",
        )

    stored_name = f"{uuid.uuid4().hex}_{filename}"
    target = UPLOAD_DIR / stored_name
    total = 0
    try:
        upload.file.seek(0)
        signature = upload.file.read(5)
        if ext == "pdf" and signature != b"%PDF-":
            raise HTTPException(status_code=400, detail=f"{filename} is not a valid PDF file.")
        elif ext in ("docx", "pptx") and not signature.startswith(b"PK\x03\x04"):
            raise HTTPException(status_code=400, detail=f"{filename} is not a valid OpenXML document.")

        upload.file.seek(0)
        with target.open("wb") as output:
            while True:
                block = upload.file.read(UPLOAD_READ_SIZE)
                if not block:
                    break
                total += len(block)
                if total > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail=f"{filename} exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)} MB upload limit.",
                    )
                output.write(block)

        # Parse before accepting; page count is checked without loading the file into memory.
        if ext == "pdf":
            with fitz.open(target) as pdf:
                if pdf.needs_pass:
                    raise HTTPException(status_code=400, detail=f"{filename} is password-protected.")
                if len(pdf) == 0:
                    raise HTTPException(status_code=400, detail=f"{filename} contains no pages.")
                if len(pdf) > MAX_PDF_PAGES:
                    raise HTTPException(
                        status_code=413,
                        detail=f"{filename} has {len(pdf)} pages; the page limit is {MAX_PDF_PAGES} pages.",
                    )
        else:
            page_count, _, err = extract_document(target)
            if err and page_count == 0:
                raise HTTPException(status_code=400, detail=f"{filename} could not be parsed: {err}")
            if page_count > MAX_PDF_PAGES:
                raise HTTPException(
                    status_code=413,
                    detail=f"{filename} has {page_count} pages; the page limit is {MAX_PDF_PAGES} pages.",
                )
        return target, stored_name
    except HTTPException:
        try:
            target.unlink(missing_ok=True)
        except PermissionError:
            gc.collect()
            try:
                target.unlink(missing_ok=True)
            except Exception:
                pass
        raise
    except (fitz.FileDataError, RuntimeError, ValueError) as exc:
        try:
            target.unlink(missing_ok=True)
        except PermissionError:
            gc.collect()
            try:
                target.unlink(missing_ok=True)
            except Exception:
                pass
        raise HTTPException(status_code=400, detail=f"{filename} is not a readable PDF.") from exc


def extract_pdf(path: Path) -> tuple[int, list[tuple[int, str]], str | None]:
    return extract_document(path)


@router.post("/upload", response_model=list[DocumentResponse], status_code=status.HTTP_201_CREATED, summary="Upload one or more PDF documents")
def upload_documents(files: list[UploadFile] = File(...), db: Session = Depends(get_db)) -> list[Document]:
    if not files:
        raise HTTPException(status_code=400, detail="Select at least one PDF file to upload.")

    created: list[Document] = []
    stored_paths: list[Path] = []
    try:
        for upload in files:
            filename = safe_filename(upload.filename)
            if not is_supported_document(filename):
                raise HTTPException(
                    status_code=400,
                    detail=f"{filename} is not a supported file type (supported: PDF, Word DOCX/DOC, PowerPoint PPTX/PPT).",
                )

            path, stored_name = store_upload(upload)
            stored_paths.append(path)
            page_count, extracted_pages, extraction_error = extract_pdf(path)
            has_text = any(bool(text) for _, text in extracted_pages)
            if extraction_error:
                extraction_status = "failed" if page_count == 0 else "warning"
                message = extraction_error
            elif not has_text:
                extraction_status = "warning"
                message = extraction_message_for("warning", filename)
            else:
                extraction_status = "completed"
                message = None

            document = Document(
                filename=filename,
                stored_filename=stored_name,
                page_count=page_count,
                extracted_page_count=sum(bool(text) for _, text in extracted_pages),
                has_extractable_text=has_text,
                extraction_status=extraction_status,
                extraction_message=message,
            )
            db.add(document)
            db.flush()
            for page_number, text in extracted_pages:
                db.add(PageText(document_id=document.id, page_number=page_number, text=text, character_count=len(text)))
            created.append(document)
        db.commit()
    except Exception:
        db.rollback()
        for path in stored_paths:
            path.unlink(missing_ok=True)
        raise
    for document in created:
        db.refresh(document)
    return created


def _document_response(db: Session, document: Document) -> DocumentResponse:
    chunks_count = int(db.scalar(select(func.count()).select_from(Chunk).where(Chunk.document_id == document.id)) or 0)
    faiss_exists, metadata_exists = document_index_exists(document.id)
    return DocumentResponse(
        id=document.id,
        filename=document.filename,
        page_count=document.page_count,
        has_extractable_text=document.has_extractable_text,
        extraction_status=document.extraction_status,
        extraction_message=document.extraction_message,
        uploaded_at=document.uploaded_at,
        extracted_page_count=document.extracted_page_count,
        is_indexed=chunks_count > 0 and (faiss_exists or fts_entry_count(db, document.id) > 0),
        chunks_count=chunks_count,
        faiss_index_exists=faiss_exists,
        metadata_exists=metadata_exists,
    )


def _index_one_document(db: Session, document: Document) -> IndexDocumentResponse:
    pages_with_text = int(
        db.scalar(
            select(func.count())
            .select_from(PageText)
            .where(PageText.document_id == document.id, PageText.character_count > 0)
        )
        or 0
    )
    if document.extraction_status != "completed" or not document.has_extractable_text or pages_with_text == 0:
        raise HTTPException(
            status_code=400,
            detail="This document has no searchable text. It may be scanned or image-based.",
        )

    drafts = create_chunk_drafts_for_document(db, document.id)
    if not drafts:
        raise HTTPException(
            status_code=400,
            detail="This document has no searchable chunks. Try a longer readable text-based PDF.",
        )
    
    # Stage replacement rows and files while the previous index remains searchable.
    temp_dir = Path(tempfile.mkdtemp(prefix=f"document_{document.id}_", dir=embedding_service.INDEX_DIR))
    index_path = temp_dir / f"document_{document.id}.faiss"
    metadata_path = temp_dir / f"document_{document.id}.json"
    final_index = embedding_service.INDEX_DIR / f"document_{document.id}.faiss"
    final_metadata = embedding_service.INDEX_DIR / f"document_{document.id}.json"
    backup_index = temp_dir / "previous.faiss"
    backup_metadata = temp_dir / "previous.json"
    index_backed_up = metadata_backed_up = False
    index_installed = metadata_installed = False
    try:
        chunks = save_chunks(db, drafts)
        faiss_created = build_document_faiss_index(document, chunks, index_path, metadata_path)
        if not faiss_created or not index_path.exists() or not metadata_path.exists():
            raise RuntimeError("The replacement semantic index was not created completely.")

        db.execute(sqltext("DELETE FROM chunk_fts WHERE document_id = :did"), {"did": document.id})
        new_chunk_ids = [chunk.id for chunk in chunks]
        old_chunk_ids = select(Chunk.id).where(
            Chunk.document_id == document.id,
            Chunk.id.not_in(new_chunk_ids),
        )
        db.execute(update(Flashcard).where(Flashcard.chunk_id.in_(old_chunk_ids)).values(chunk_id=None))
        db.execute(
            delete(Chunk).where(
                Chunk.document_id == document.id,
                Chunk.id.not_in(new_chunk_ids),
            )
        )
        insert_chunk_fts_entries(db, chunks, commit=False)

        if final_index.exists():
            os.replace(final_index, backup_index)
            index_backed_up = True
        if final_metadata.exists():
            os.replace(final_metadata, backup_metadata)
            metadata_backed_up = True
        os.replace(index_path, final_index)
        index_installed = True
        os.replace(metadata_path, final_metadata)
        metadata_installed = True
        db.commit()
    except ImportError:
        db.rollback()
        if index_installed:
            final_index.unlink(missing_ok=True)
        if metadata_installed:
            final_metadata.unlink(missing_ok=True)
        if index_backed_up:
            os.replace(backup_index, final_index)
        if metadata_backed_up:
            os.replace(backup_metadata, final_metadata)
        raise HTTPException(status_code=503, detail="Semantic indexing dependencies are not installed.") from None
    except Exception as exc:
        db.rollback()
        if index_installed:
            final_index.unlink(missing_ok=True)
        if metadata_installed:
            final_metadata.unlink(missing_ok=True)
        if index_backed_up:
            os.replace(backup_index, final_index)
        if metadata_backed_up:
            os.replace(backup_metadata, final_metadata)
        raise HTTPException(status_code=500, detail=f"Indexing failed; the previous index was retained: {exc.__class__.__name__}.") from exc
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
    return IndexDocumentResponse(
        document_id=document.id,
        filename=document.filename,
        status="indexed",
        pages_with_text=pages_with_text,
        chunks_created=len(chunks),
        faiss_index_created=faiss_created,
        keyword_index_created=fts_entry_count(db, document.id) == len(chunks),
        message=f"Indexed {document.filename} with {len(chunks)} chunks.",
    )


@router.post("/index-all", response_model=IndexAllResponse, summary="Index all eligible documents")
def index_all_documents(db: Session = Depends(get_db)) -> IndexAllResponse:
    documents = list(db.scalars(select(Document).order_by(Document.uploaded_at.desc())).all())
    results: list[IndexDocumentResponse] = []
    failures = 0
    for document in documents:
        try:
            results.append(_index_one_document(db, document))
        except HTTPException as exc:
            db.rollback()
            failures += 1
            results.append(
                IndexDocumentResponse(
                    document_id=document.id,
                    filename=document.filename,
                    status="warning",
                    pages_with_text=0,
                    chunks_created=0,
                    faiss_index_created=False,
                    keyword_index_created=False,
                    message=str(exc.detail),
                )
            )
    return IndexAllResponse(
        results=results,
        indexed_document_count=sum(1 for item in results if item.status == "indexed"),
        failed_or_warning_count=failures,
        total_chunks_created=sum(item.chunks_created for item in results),
    )


@router.post("/{document_id}/index", response_model=IndexDocumentResponse, summary="Index a document for keyword and semantic search")
def index_document(document_id: int, db: Session = Depends(get_db)) -> IndexDocumentResponse:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    return _index_one_document(db, document)


@router.get("", response_model=list[DocumentResponse], summary="List all uploaded documents")
def list_documents(db: Session = Depends(get_db)) -> list[DocumentResponse]:
    documents = list(db.scalars(select(Document).order_by(Document.uploaded_at.desc())).all())
    return [_document_response(db, document) for document in documents]


@router.get("/{document_id}", response_model=DocumentDetailResponse, summary="Get document details by ID")
def get_document(document_id: int, db: Session = Depends(get_db)) -> DocumentResponse:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    return _document_response(db, document)


@router.get("/{document_id}/pages", response_model=list[PageTextResponse], summary="Get extracted pages for a document")
def get_document_pages(document_id: int, include_text: bool = True, db: Session = Depends(get_db)) -> list[PageTextResponse]:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    pages = list(db.scalars(select(PageText).where(PageText.document_id == document_id).order_by(PageText.page_number)).all())
    if include_text:
        return [PageTextResponse.model_validate(page) for page in pages]
    return [PageTextResponse(page_number=page.page_number, character_count=page.character_count, text=None) for page in pages]


@router.delete("/{document_id}", response_model=DeleteDocumentResponse, summary="Delete a document and its extracted text")
def delete_document(document_id: int, db: Session = Depends(get_db)) -> DeleteDocumentResponse:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    
    errors: list[str] = []
    index_path = embedding_service.INDEX_DIR / f"document_{document_id}.faiss"
    metadata_path = embedding_service.INDEX_DIR / f"document_{document_id}.json"
    file_path = UPLOAD_DIR / document.stored_filename
    file_deleted = index_deleted = metadata_deleted = False
    for path, label in ((file_path, "uploaded file"), (index_path, "FAISS index"), (metadata_path, "FAISS metadata")):
        try:
            existed = path.exists()
            path.unlink(missing_ok=True)
            if label == "uploaded file":
                file_deleted = existed
            elif label == "FAISS index":
                index_deleted = existed
            else:
                metadata_deleted = existed
        except OSError as exc:
            errors.append(f"Could not remove {label}: {exc.__class__.__name__}.")

    chunks_deleted = fts_deleted = False
    if not errors:
        try:
            db.execute(sqltext("DELETE FROM chunk_fts WHERE document_id = :did"), {"did": document_id})
            fts_deleted = True
            card_ids = select(Flashcard.id).where(Flashcard.document_id == document_id)
            db.execute(delete(StudyLog).where(StudyLog.card_id.in_(card_ids)))
            db.execute(delete(Flashcard).where(Flashcard.document_id == document_id))
            db.execute(delete(Chunk).where(Chunk.document_id == document_id))
            chunks_deleted = True
            db.delete(document)
            db.commit()
        except Exception as exc:
            db.rollback()
            chunks_deleted = fts_deleted = False
            errors.append(f"Could not remove document database records: {exc.__class__.__name__}.")

    if errors:
        retained = db.get(Document, document_id)
        if retained is not None:
            retained.deletion_status = "partial"
            retained.deletion_error = " ".join(errors)
            db.commit()
    
    return DeleteDocumentResponse(
        message=("Document and related data were deleted." if not errors else
                 "Cleanup was incomplete. The document record was retained so cleanup can be retried."),
        document_id=document_id,
        cleanup_complete=not errors,
        cleanup_errors=errors,
        file_deleted=file_deleted,
        chunks_deleted=chunks_deleted,
        keyword_entries_deleted=fts_deleted,
        faiss_index_deleted=index_deleted,
        metadata_deleted=metadata_deleted,
    )
