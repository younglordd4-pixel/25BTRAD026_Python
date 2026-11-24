from __future__ import annotations
import json
import math
from typing import Any, NamedTuple
from sqlalchemy import text as sqltext
from sqlalchemy.orm import Session

import faiss
import numpy as np
from ..database import INDEX_DIR
from ..models import Chunk, Document
from .embedding_service import EmbeddingModel, document_index_exists

# Constants for Hybrid Search
SEMANTIC_WEIGHT = 0.65
KEYWORD_WEIGHT = 0.35

class SearchCandidate(NamedTuple):
    chunk_id: int
    document_id: int
    filename: str
    page_number: int
    chunk_number: int
    text: str
    semantic_score: float | None = None
    keyword_score: float | None = None

def ensure_fts_table(db: Session) -> None:
    """Ensures the FTS5 virtual table exists."""
    db.execute(sqltext("""
        CREATE VIRTUAL TABLE IF NOT EXISTS chunk_fts USING fts5(
            chunk_id UNINDEXED,
            document_id UNINDEXED,
            page_number UNINDEXED,
            text
        )
    """))
    db.commit()


def insert_chunk_fts_entries(db: Session, chunks: list[Chunk], commit: bool = True) -> None:
    """Inserts chunks into the FTS5 virtual table."""
    try:
        for chunk in chunks:
            db.execute(
                sqltext("INSERT INTO chunk_fts (chunk_id, document_id, page_number, text) VALUES (:cid, :did, :pn, :txt)"),
                {"cid": chunk.id, "did": chunk.document_id, "pn": chunk.page_number, "txt": chunk.text}
            )
        if commit:
            db.commit()
    except Exception:
        if not commit:
            raise
        db.rollback()
        ensure_fts_table(db)
        for chunk in chunks:
            db.execute(
                sqltext("INSERT INTO chunk_fts (chunk_id, document_id, page_number, text) VALUES (:cid, :did, :pn, :txt)"),
                {"cid": chunk.id, "did": chunk.document_id, "pn": chunk.page_number, "txt": chunk.text}
            )
        if commit:
            db.commit()


def fts_entry_count(db: Session, document_id: int) -> int:
    """Returns count of FTS5 entries for a document."""
    try:
        result = db.execute(
            sqltext("SELECT count(*) FROM chunk_fts WHERE document_id = :did"),
            {"did": document_id}
        ).scalar()
        return int(result or 0)
    except Exception:
        ensure_fts_table(db)
        return 0


def delete_document_chunks(db: Session, document_id: int) -> None:
    """Removes chunks and FTS5 entries for a document."""
    try:
        db.execute(sqltext("DELETE FROM chunk_fts WHERE document_id = :did"), {"did": document_id})
    except Exception:
        ensure_fts_table(db)
    db.execute(sqltext("DELETE FROM chunks WHERE document_id = :did"), {"did": document_id})
    db.commit()

def _sanitize_fts_query(query: str) -> str:
    """Escapes special FTS5 characters to prevent crashes."""
    # FTS5 queries are sensitive to quotes and special operators. 
    # We wrap in double quotes and escape existing double quotes.
    escaped = query.replace('"', '""')
    return f'"{escaped}"'

def keyword_search(db: Session, query: str, document_ids: list[int] | None, top_k: int) -> list[SearchCandidate]:
    """Performs exact keyword/formula search using FTS5 BM25."""
    safe_query = _sanitize_fts_query(query) if any(c in query for c in "()[]{}*=:\"-+^~") else query
    
    where_clauses = ["text MATCH :q"]
    params: dict[str, Any] = {"q": safe_query, "limit": top_k * 2}
    
    if document_ids:
        placeholders = ", ".join(f":id_{i}" for i in range(len(document_ids)))
        where_clauses.append(f"document_id IN ({placeholders})")
        for i, doc_id in enumerate(document_ids):
            params[f"id_{i}"] = doc_id
            
    sql = f"SELECT chunk_id, document_id, page_number, text, rank FROM chunk_fts WHERE {' AND '.join(where_clauses)} ORDER BY rank LIMIT :limit"
    
    try:
        results = db.execute(sqltext(sql), params).all()
    except Exception:
        try:
            params["q"] = _sanitize_fts_query(query)
            results = db.execute(sqltext(sql), params).all()
        except Exception:
            return []

    candidates = []
    for row in results:
        chunk = db.get(Chunk, row[0])
        doc = db.get(Document, row[1])
        candidates.append(SearchCandidate(
            chunk_id=row[0],
            document_id=row[1],
            filename=doc.filename if doc else "Unknown",
            page_number=row[2],
            chunk_number=chunk.chunk_number if chunk else 1,
            text=row[3],
            keyword_score=float(row[4]) if row[4] is not None else 0.0
        ))
    return candidates

def semantic_search(query: str, document_ids: list[int] | None, top_k: int) -> list[SearchCandidate]:
    """Performs meaning-based search using FAISS."""
    model = EmbeddingModel.get_model()
    q_emb = model.encode([query], convert_to_numpy=True).astype("float32")
    faiss.normalize_L2(q_emb)
    
    all_candidates = []
    
    # Identify which documents to search
    target_docs = document_ids if document_ids else [] 
    # If no IDs provided, we should ideally search all indexed docs. 
    # For now, we check what exists in the directory.
    if not target_docs:
        target_docs = [int(f.stem.split("_")[1]) for f in INDEX_DIR.glob("document_*.faiss")]

    for doc_id in target_docs:
        faiss_path = INDEX_DIR / f"document_{doc_id}.faiss"
        meta_path = INDEX_DIR / f"document_{doc_id}.json"
        
        if not (faiss_path.exists() and meta_path.exists()):
            continue
            
        index = faiss.read_index(str(faiss_path))
        with open(meta_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
            
        scores, indices = index.search(q_emb, k=top_k * 2)
        
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1: continue
            meta = metadata[idx]
            all_candidates.append(SearchCandidate(
                chunk_id=meta["chunk_id"],
                document_id=meta["document_id"],
                filename=meta["filename"],
                page_number=meta["page_number"],
                chunk_number=meta["chunk_number"],
                text="", # Filled later from DB to avoid loading everything into memory
                semantic_score=float(score)
            ))
            
    # Sort all candidates by score descending and take top k*2
    all_candidates.sort(key=lambda x: x.semantic_score or 0.0, reverse=True)
    return all_candidates[:top_k * 2]

def is_definition_query(query: str) -> bool:
    """Detects if query is requesting a definition or meaning."""
    import re
    return bool(re.search(r"\b(define|definition|what is|what are|meaning of|explain|describe)\b", query, re.IGNORECASE))


def hybrid_search(db: Session, query: str, document_ids: list[int] | None, top_k: int) -> list[SearchCandidate]:
    """
    Combines FTS5 BM25 and FAISS vector results with dynamic intent-aware weighting.
    - If query is definitional ('define X', 'what is X'), awards higher weight to exact term matches.
    - Grants a synergy bonus (15%) to candidates appearing in both semantic and keyword results.
    - Grants a definitional bonus (10%) to chunks containing canonical definition patterns for the query topic.
    """
    import re
    # 1. Get candidates from both modes
    k_cands = keyword_search(db, query, document_ids, top_k * 2)
    s_cands = semantic_search(query, document_ids, top_k * 2)
    
    # 2. Adjust weights based on query intent
    is_def = is_definition_query(query)
    sem_weight = 0.60 if is_def else SEMANTIC_WEIGHT
    kw_weight = 0.40 if is_def else KEYWORD_WEIGHT
    
    # Extract query concept for bonus scoring
    q_concept = re.sub(r"\b(define|definition|what is|what are|meaning of|explain|describe|an|a|the)\b", "", query, flags=re.IGNORECASE).strip()
    concept_words = [w.lower() for w in q_concept.split() if len(w) > 2]
    
    # Helper to normalize scores to 0-1
    def normalize(scores: list[float], reverse=False):
        if not scores: return []
        s_min, s_max = min(scores), max(scores)
        if s_max == s_min: return [1.0] * len(scores)
        normalized = []
        for s in scores:
            val = (s - s_min) / (s_max - s_min)
            normalized.append(1.0 - val if reverse else val)
        return normalized

    k_raw = [c.keyword_score for c in k_cands if c.keyword_score is not None]
    s_raw = [c.semantic_score for c in s_cands if c.semantic_score is not None]
    
    k_norm = normalize(k_raw, reverse=True) # BM25: lower is better
    s_norm = normalize(s_raw, reverse=False) # FAISS: higher is better
    
    k_score_map = {c.chunk_id: score for c, score in zip(k_cands, k_norm)}
    s_score_map = {c.chunk_id: score for c, score in zip(s_cands, s_norm)}
    
    all_ids = set(k_score_map.keys()) | set(s_score_map.keys())
    scored_candidates: list[tuple[float, SearchCandidate]] = []
    
    for cid in all_ids:
        chunk = db.get(Chunk, cid)
        if not chunk: continue
        doc = db.get(Document, chunk.document_id)
        
        s_score = s_score_map.get(cid, 0.0)
        k_score = k_score_map.get(cid, 0.0)
        
        base_score = (sem_weight * s_score) + (kw_weight * k_score)
        
        # Synergy bonus: chunk matched both semantic and keyword search
        if cid in s_score_map and cid in k_score_map:
            base_score += 0.15
            
        # Definitional pattern bonus
        chunk_lower = chunk.text.lower()
        if is_def and any(cw in chunk_lower for cw in concept_words):
            if any(p in chunk_lower for p in ["is defined as", "is a system program", "is a program that", "refers to", "acts as an interface"]):
                base_score += 0.20
            elif " is " in chunk_lower:
                base_score += 0.08
                
        candidate = SearchCandidate(
            chunk_id=cid,
            document_id=chunk.document_id,
            filename=doc.filename if doc else "Unknown",
            page_number=chunk.page_number,
            chunk_number=chunk.chunk_number,
            text=chunk.text,
            semantic_score=s_score if cid in s_score_map else None,
            keyword_score=k_score if cid in k_score_map else None,
        )
        scored_candidates.append((base_score, candidate))
        
    scored_candidates.sort(key=lambda x: x[0], reverse=True)
    return [cand for _, cand in scored_candidates[:top_k]]


def related_pages(current_page: int, total_pages: int) -> list[int]:
    """Returns sorted list of surrounding page numbers."""
    pages = {current_page}
    if current_page > 1:
        pages.add(current_page - 1)
    if current_page < total_pages:
        pages.add(current_page + 1)
    return sorted(pages)
