from __future__ import annotations
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select, text as sqltext
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Chunk, Document, PageText
from ..schemas import (
    SearchRequest,
    SearchResponse,
    SearchResultResponse,
    DirectAnswerResponse,
    DocumentDebugResponse,
    ChunkPreviewResponse,
)
from ..services import search_service

router = APIRouter(prefix="/search", tags=["Search"])

def _norm_keyword_score(raw: float | None) -> float:
    """Converts a raw FTS5 BM25 rank (negative, lower-is-better) to 0-1 (higher-is-better)."""
    if raw is None:
        return 0.0
    # BM25 rank is negative in SQLite FTS5; convert to positive relevance
    return 1.0 / (1.0 + abs(raw))


def build_search_result(rank: int, cand: search_service.SearchCandidate, doc_page_count: int) -> SearchResultResponse:
    s_score = cand.semantic_score
    k_raw = cand.keyword_score
    # Normalise BM25 rank to 0-1 for display and scoring purposes
    k_score_norm = _norm_keyword_score(k_raw) if k_raw is not None else None

    final_score = (search_service.SEMANTIC_WEIGHT * (s_score or 0.0)) + (search_service.KEYWORD_WEIGHT * (k_score_norm or 0.0))

    s_pct = (s_score * 100) if s_score is not None else None
    k_pct = (k_score_norm * 100) if k_score_norm is not None else None
    f_pct = final_score * 100

    matched_by = "hybrid"
    if s_score is not None and k_raw is None: matched_by = "semantic"
    elif k_raw is not None and s_score is None: matched_by = "keyword"
    
    related = []
    if cand.page_number > 1: related.append(cand.page_number - 1)
    related.append(cand.page_number)
    if cand.page_number < doc_page_count: related.append(cand.page_number + 1)
    
    return SearchResultResponse(
        rank=rank,
        chunk_id=cand.chunk_id,
        document_id=cand.document_id,
        filename=cand.filename,
        page_number=cand.page_number,
        chunk_number=cand.chunk_number,
        text=cand.text,
        snippet=cand.text[:200] + "..." if len(cand.text) > 200 else cand.text,
        semantic_score=s_score,
        semantic_score_percent=s_pct,
        keyword_score=k_score_norm,
        keyword_score_percent=k_pct,
        final_score=final_score,
        final_score_percent=f_pct,
        matched_by=matched_by,
        related_pages=related
    )

@router.post("", response_model=SearchResponse, summary="Search indexed documents")
def search_documents(request: SearchRequest, db: Session = Depends(get_db)) -> SearchResponse:
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Search query cannot be blank.")
    
    indexed_docs_count = db.scalar(sqltext("SELECT count(DISTINCT document_id) FROM chunks")) or 0
    if indexed_docs_count == 0:
        return SearchResponse(
            query=query,
            mode=request.mode,
            total_candidates=0,
            returned_results=0,
            results=[],
            message="No indexed documents are available. Upload and index a readable text-based PDF first."
        )

    if request.mode == "semantic":
        candidates = search_service.semantic_search(query, request.document_ids, request.top_k)
        for i, c in enumerate(candidates):
            chunk = db.get(Chunk, c.chunk_id)
            if chunk: 
                candidates[i] = c._replace(text=chunk.text)
    elif request.mode == "keyword":
        candidates = search_service.keyword_search(db, query, request.document_ids, request.top_k)
    else: # hybrid
        candidates = search_service.hybrid_search(db, query, request.document_ids, request.top_k)

    filtered_results = []
    raw_candidates_count = len(candidates)
    
    for i, cand in enumerate(candidates, start=1):
        # Normalise BM25 keyword score before scoring (FTS5 rank is negative)
        k_norm = _norm_keyword_score(cand.keyword_score) if cand.keyword_score is not None else 0.0
        score = (search_service.SEMANTIC_WEIGHT * (cand.semantic_score or 0.0)) + (search_service.KEYWORD_WEIGHT * k_norm)
        if score >= request.min_score:
            doc = db.get(Document, cand.document_id)
            filtered_results.append(build_search_result(i, cand, doc.page_count if doc else 0))

    message = "Search completed successfully."
    filtered_by_min_score = False
    if raw_candidates_count > 0 and not filtered_results:
        filtered_by_min_score = True
        message = "Matches were found, but none met the selected minimum relevance. Lower the minimum relevance to see them."

    # Synthesize direct answer from the top retrieved results
    direct_answer_payload = None
    if filtered_results:
        chunks_payload = [
            {
                "text": r.text,
                "page_number": r.page_number,
                "filename": r.filename,
                "score": r.final_score,
            }
            for r in filtered_results[:4]
        ]
        from ..services.answer_service import generate_direct_answer
        gen = generate_direct_answer(query, chunks_payload)
        direct_answer_payload = DirectAnswerResponse(
            direct_answer=gen.direct_answer,
            key_points=gen.key_points,
            confidence=gen.confidence,
            primary_source_page=gen.primary_source_page,
            primary_source_filename=gen.primary_source_filename,
        )

    debug = None
    if request.include_debug:
        debug = {
            "selected_document_ids": request.document_ids,
            "semantic_candidate_count": len(candidates) if request.mode == "semantic" else "N/A",
            "keyword_candidate_count": len(candidates) if request.mode == "keyword" else "N/A",
            "merged_candidate_count": len(candidates) if request.mode == "hybrid" else "N/A",
            "applied_min_score": request.min_score
        }

    return SearchResponse(
        query=query,
        mode=request.mode,
        total_candidates=raw_candidates_count,
        returned_results=len(filtered_results),
        results=filtered_results,
        message=message,
        filtered_by_min_score=filtered_by_min_score,
        direct_answer=direct_answer_payload,
        debug=debug
    )

@router.get("/debug/document/{document_id}", response_model=DocumentDebugResponse, summary="Get indexing debug info for a document")
def debug_document(document_id: int, db: Session = Depends(get_db)) -> DocumentDebugResponse:
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    
    chunks = db.query(Chunk).filter(Chunk.document_id == document_id).all()
    faiss_exists, meta_exists = search_service.document_index_exists(document_id)
    fts_count = search_service.fts_entry_count(db, document_id)
    
    previews = [
        ChunkPreviewResponse(
            source_filename=doc.filename,
            page_number=c.page_number,
            chunk_number=c.chunk_number,
            preview=c.text[:250]
        ) for c in chunks[:3]
    ]
    
    return DocumentDebugResponse(
        document_id=doc.id,
        filename=doc.filename,
        page_count=doc.page_count,
        page_text_count=db.scalar(sqltext("SELECT count(*) FROM page_text WHERE document_id = :did"), {"did": document_id}) or 0,
        chunks_count=len(chunks),
        faiss_index_exists=faiss_exists,
        metadata_exists=meta_exists,
        fts5_entries_count=fts_count,
        first_chunk_previews=previews
    )
