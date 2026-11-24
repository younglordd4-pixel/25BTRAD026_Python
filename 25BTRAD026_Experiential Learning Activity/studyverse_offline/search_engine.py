"""
search_engine.py — StudyVerse Offline
======================================
All search logic: chunking, keyword (FTS5 / fallback), semantic (FAISS),
and hybrid ranking.

Public API
----------
Chunking
    chunk_page_text(doc_id, filename, page_num, text) -> list[dict]

Index building
    build_index(conn, doc_id, fts5_available, model) -> dict

Search
    keyword_search(conn, query, doc_ids, top_k, fts5_available) -> list[dict]
    semantic_search(model, doc_ids, query, top_k)              -> list[dict]
    hybrid_search(conn, model, query, doc_ids, top_k, fts5_available) -> list[dict]

Each result dict has the keys:
    chunk_id, document_id, filename, page_number, chunk_number,
    text, semantic_score, keyword_score, final_score
    (scores are all in [0, 1] — already normalised)
"""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

import os
import sys
from pathlib import Path

# Add faiss_cpu.libs to DLL directory on Windows
_dll_handles = []
for base in (Path(__file__).resolve().parents[1], Path(__file__).resolve().parent):
    for candidate in (base / "backend" / ".venv" / "Lib" / "site-packages" / "faiss_cpu.libs", base / ".venv" / "Lib" / "site-packages" / "faiss_cpu.libs"):
        if candidate.is_dir():
            if hasattr(os, "add_dll_directory"):
                try:
                    _dll_handles.append(os.add_dll_directory(str(candidate)))
                except Exception:
                    pass
            os.environ["PATH"] = str(candidate) + os.pathsep + os.environ.get("PATH", "")

import faiss
import numpy as np
import streamlit as st
from sentence_transformers import SentenceTransformer

from database import (
    INDEX_DIR,
    delete_chunks_for_document,
    get_chunks_by_ids,
    get_page_texts,
    insert_chunks,
    insert_fts5_entries,
    get_all_chunks_for_docs,
)

# ── Hybrid weights (exact spec values) ────────────────────────────────────────
SEMANTIC_WEIGHT = 0.70
KEYWORD_WEIGHT  = 0.30

# ── Chunking parameters ────────────────────────────────────────────────────────
CHUNK_SIZE   = 700   # target character window
CHUNK_OVERLAP = 120  # overlap between consecutive chunks
CHUNK_MIN     = 150  # minimum chunk length to keep


# ═══════════════════════════════════════════════════════════════════════════════
# A.  MODEL (cached across Streamlit reruns)
# ═══════════════════════════════════════════════════════════════════════════════
@st.cache_resource(show_spinner="Loading language model (first run only)…")
def load_model() -> SentenceTransformer:
    """Load SentenceTransformer once per Streamlit session."""
    return SentenceTransformer("all-MiniLM-L6-v2")


# ═══════════════════════════════════════════════════════════════════════════════
# B.  CHUNKING
# ═══════════════════════════════════════════════════════════════════════════════
def _normalize_whitespace(text: str) -> str:
    """Collapse runs of whitespace/newlines to a single space, strip ends."""
    return re.sub(r"\s+", " ", text).strip()


def _best_break(text: str, target: int) -> int:
    """
    Find the best character position to end a chunk near *target*.
    Priority: sentence terminator > newline > space > hard cut.
    Search window: last 120 characters before *target*.
    """
    window_start = max(0, target - 120)
    window = text[window_start:target]

    # Priority 1: sentence terminators followed by whitespace or end-of-window
    for i in range(len(window) - 1, -1, -1):
        if window[i] in ".!?" and (i + 1 >= len(window) or window[i + 1].isspace()):
            return window_start + i + 1

    # Priority 2: any whitespace
    for i in range(len(window) - 1, -1, -1):
        if window[i].isspace():
            return window_start + i + 1

    # Fallback: hard cut at target
    return target


def chunk_page_text(
    doc_id: int,
    filename: str,
    page_number: int,
    text: str,
) -> list[dict]:
    """
    Deterministically split *text* into overlapping character chunks.

    Each returned dict:
        document_id, filename, page_number, chunk_number,
        text, character_count
    """
    if not text:
        return []

    norm = _normalize_whitespace(text)
    total = len(norm)
    if total == 0:
        return []

    chunks: list[dict] = []
    start = 0
    chunk_num = 0

    while start < total:
        raw_end = min(start + CHUNK_SIZE, total)
        end = _best_break(norm, raw_end) if raw_end < total else raw_end

        chunk_text = norm[start:end].strip()

        if len(chunk_text) >= CHUNK_MIN:
            chunk_num += 1
            chunks.append(
                {
                    "document_id":     doc_id,
                    "filename":        filename,
                    "page_number":     page_number,
                    "chunk_number":    chunk_num,
                    "text":            chunk_text,
                    "character_count": len(chunk_text),
                }
            )
        elif chunk_num == 0 and total >= 30:
            # Very short page — keep it as one chunk even if below CHUNK_MIN
            chunk_num += 1
            chunks.append(
                {
                    "document_id":     doc_id,
                    "filename":        filename,
                    "page_number":     page_number,
                    "chunk_number":    chunk_num,
                    "text":            norm,
                    "character_count": total,
                }
            )
            break

        # Advance start: move forward by (chunk_size - overlap) but at least 50 chars
        step = max(end - start - CHUNK_OVERLAP, 50)
        start += step
        if start >= total:
            break

    return chunks


# ═══════════════════════════════════════════════════════════════════════════════
# C.  KEYWORD SEARCH  (FTS5 BM25 or frequency fallback)
# ═══════════════════════════════════════════════════════════════════════════════
def _sanitize_fts_query(query: str) -> str:
    """
    Escape characters that would crash FTS5.
    Wrap the entire query in double-quotes (phrase match).
    Internal double-quotes are doubled to escape them.
    """
    escaped = query.replace('"', '""')
    return f'"{escaped}"'


def _fts5_keyword_search(
    conn: sqlite3.Connection,
    query: str,
    doc_ids: list[int] | None,
    top_k: int,
) -> list[dict]:
    """FTS5 BM25 keyword search.  Returns raw BM25 scores (lower = better)."""
    # Decide whether to phrase-quote (needed for special characters)
    needs_quoting = any(c in query for c in r'()[]{}*=:"-+^~!')
    safe_q = _sanitize_fts_query(query) if needs_quoting else query

    where_parts = ["text MATCH ?"]
    params: list = [safe_q]

    if doc_ids:
        placeholders = ",".join("?" * len(doc_ids))
        where_parts.append(f"document_id IN ({placeholders})")
        params.extend(doc_ids)

    params.append(top_k * 3)  # fetch extra candidates for better pool
    sql = (
        f"SELECT chunk_id, document_id, page_number, text, rank "
        f"FROM chunk_fts "
        f"WHERE {' AND '.join(where_parts)} "
        f"ORDER BY rank LIMIT ?"
    )

    try:
        rows = conn.execute(sql, params).fetchall()
    except sqlite3.OperationalError:
        # Phrase-quoted fallback on error
        try:
            params[0] = _sanitize_fts_query(query)
            rows = conn.execute(sql, params).fetchall()
        except sqlite3.OperationalError:
            return []

    results = []
    for row in rows:
        chunk_id, document_id, page_number, text, rank = (
            row["chunk_id"], row["document_id"], row["page_number"],
            row["text"], row["rank"]
        )
        chunk_map = get_chunks_by_ids(conn, [chunk_id])
        chunk = chunk_map.get(chunk_id, {})
        results.append(
            {
                "chunk_id":      chunk_id,
                "document_id":   document_id,
                "filename":      chunk.get("filename", "Unknown"),
                "page_number":   page_number,
                "chunk_number":  chunk.get("chunk_number", 1),
                "text":          text,
                "keyword_score": float(rank) if rank is not None else 0.0,
                "semantic_score": None,
            }
        )
    return results


def _fallback_keyword_search(
    conn: sqlite3.Connection,
    query: str,
    doc_ids: list[int] | None,
    top_k: int,
) -> list[dict]:
    """
    Case-insensitive term-frequency fallback when FTS5 is unavailable.
    Score = number of times any query token appears in the chunk text.
    """
    terms = [t.lower() for t in re.split(r"\s+", query.strip()) if t]
    if not terms:
        return []

    all_chunks = get_all_chunks_for_docs(conn, doc_ids)
    scored: list[tuple[float, dict]] = []

    for chunk in all_chunks:
        chunk_lower = chunk["text"].lower()
        score = sum(chunk_lower.count(t) for t in terms)
        if score > 0:
            scored.append(
                (
                    float(score),
                    {
                        "chunk_id":      chunk["id"],
                        "document_id":   chunk["document_id"],
                        "filename":      chunk["filename"],
                        "page_number":   chunk["page_number"],
                        "chunk_number":  chunk["chunk_number"],
                        "text":          chunk["text"],
                        "keyword_score": float(score),
                        "semantic_score": None,
                    },
                )
            )

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[: top_k * 3]]


def keyword_search(
    conn: sqlite3.Connection,
    query: str,
    doc_ids: list[int] | None,
    top_k: int,
    fts5_available: bool,
) -> list[dict]:
    """
    Route to FTS5 or fallback keyword search.
    Returns results with raw (un-normalised) keyword_score.
    """
    if not query.strip():
        return []
    if fts5_available:
        return _fts5_keyword_search(conn, query, doc_ids, top_k)
    return _fallback_keyword_search(conn, query, doc_ids, top_k)


# ═══════════════════════════════════════════════════════════════════════════════
# D.  SEMANTIC SEARCH  (FAISS IndexFlatIP)
# ═══════════════════════════════════════════════════════════════════════════════
def _faiss_path(doc_id: int) -> Path:
    return INDEX_DIR / f"document_{doc_id}.faiss"


def _meta_path(doc_id: int) -> Path:
    return INDEX_DIR / f"document_{doc_id}.json"


def faiss_index_exists(doc_id: int) -> bool:
    return _faiss_path(doc_id).exists() and _meta_path(doc_id).exists()


def _encode_query(model: SentenceTransformer, query: str) -> np.ndarray:
    """Encode and L2-normalise the query vector."""
    q_emb = model.encode([query], convert_to_numpy=True).astype("float32")
    faiss.normalize_L2(q_emb)
    return q_emb


def semantic_search(
    model: SentenceTransformer,
    doc_ids: list[int] | None,
    query: str,
    top_k: int,
) -> list[dict]:
    """
    Search FAISS indexes for the given query.
    Returns candidates with raw cosine-similarity semantic_score in [0, 1].
    """
    if not query.strip():
        return []

    q_emb = _encode_query(model, query)

    # Build list of doc IDs to search
    if doc_ids:
        targets = doc_ids
    else:
        targets = [
            int(p.stem.split("_")[1])
            for p in INDEX_DIR.glob("document_*.faiss")
        ]

    all_candidates: list[dict] = []

    for doc_id in targets:
        fp = _faiss_path(doc_id)
        mp = _meta_path(doc_id)
        if not (fp.exists() and mp.exists()):
            continue

        index = faiss.read_index(str(fp))
        with mp.open("r", encoding="utf-8") as f:
            metadata: list[dict] = json.load(f)

        k = min(top_k * 3, index.ntotal)
        if k == 0:
            continue

        scores, indices = index.search(q_emb, k)

        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            meta = metadata[idx]
            all_candidates.append(
                {
                    "chunk_id":      meta["chunk_id"],
                    "document_id":   meta["document_id"],
                    "filename":      meta["filename"],
                    "page_number":   meta["page_number"],
                    "chunk_number":  meta["chunk_number"],
                    "text":          "",  # filled below from DB
                    "semantic_score": float(score),
                    "keyword_score": None,
                }
            )

    if not all_candidates:
        return []

    # Sort descending and trim
    all_candidates.sort(key=lambda x: x["semantic_score"], reverse=True)
    top_cands = all_candidates[: top_k * 3]

    # Fill text from DB
    chunk_ids = [c["chunk_id"] for c in top_cands]
    # We don't have conn here; text will be filled by the caller (hybrid / direct sem)
    return top_cands


# ═══════════════════════════════════════════════════════════════════════════════
# E.  SCORE NORMALISATION
# ═══════════════════════════════════════════════════════════════════════════════
def _normalize_scores(
    items: list[dict],
    score_key: str,
    reverse: bool = False,
) -> list[dict]:
    """
    In-place min-max normalise score_key across *items*.

    reverse=True: lower raw score = higher normalised score (for BM25 rank).
    """
    values = [x[score_key] for x in items if x.get(score_key) is not None]
    if not values:
        return items

    s_min, s_max = min(values), max(values)
    for item in items:
        raw = item.get(score_key)
        if raw is None:
            item[score_key] = 0.0
            continue
        if s_max == s_min:
            item[score_key] = 1.0
        else:
            val = (raw - s_min) / (s_max - s_min)
            item[score_key] = 1.0 - val if reverse else val
    return items


# ═══════════════════════════════════════════════════════════════════════════════
# F.  HYBRID SEARCH
# ═══════════════════════════════════════════════════════════════════════════════
def hybrid_search(
    conn: sqlite3.Connection,
    model: SentenceTransformer,
    query: str,
    doc_ids: list[int] | None,
    top_k: int,
    fts5_available: bool,
) -> list[dict]:
    """
    Combine semantic and keyword results.

    final_score = (SEMANTIC_WEIGHT × normalised_semantic)
                + (KEYWORD_WEIGHT  × normalised_keyword)

    Weights: 0.70 / 0.30 (spec values).
    Scores are normalised per-request, not globally.
    """
    k_cands = keyword_search(conn, query, doc_ids, top_k, fts5_available)
    s_cands = semantic_search(model, doc_ids, query, top_k)

    # Fill text for semantic candidates from DB
    s_chunk_ids = [c["chunk_id"] for c in s_cands]
    s_text_map  = get_chunks_by_ids(conn, s_chunk_ids)
    for c in s_cands:
        db_row = s_text_map.get(c["chunk_id"], {})
        c["text"] = db_row.get("text", "")

    # Normalise scores (BM25 is reversed: lower rank = better)
    _normalize_scores(k_cands, "keyword_score",  reverse=True)
    _normalize_scores(s_cands, "semantic_score", reverse=False)

    k_map: dict[int, dict] = {c["chunk_id"]: c for c in k_cands}
    s_map: dict[int, dict] = {c["chunk_id"]: c for c in s_cands}

    all_ids = set(k_map.keys()) | set(s_map.keys())
    merged: list[dict] = []

    for cid in all_ids:
        k = k_map.get(cid)
        s = s_map.get(cid)

        # Pick the richer source for metadata
        base = s if s else k
        if not base:
            continue

        k_score = k["keyword_score"]  if k else 0.0
        s_score = s["semantic_score"] if s else 0.0

        final = SEMANTIC_WEIGHT * s_score + KEYWORD_WEIGHT * k_score

        merged.append(
            {
                "chunk_id":       cid,
                "document_id":    base["document_id"],
                "filename":       base["filename"],
                "page_number":    base["page_number"],
                "chunk_number":   base["chunk_number"],
                "text":           base["text"],
                "semantic_score": s_score if s else None,
                "keyword_score":  k_score if k else None,
                "final_score":    final,
            }
        )

    merged.sort(key=lambda x: x["final_score"], reverse=True)
    return merged[:top_k]


def keyword_only_search(
    conn: sqlite3.Connection,
    query: str,
    doc_ids: list[int] | None,
    top_k: int,
    fts5_available: bool,
) -> list[dict]:
    """Keyword-only path: returns normalised results with final_score = keyword_score."""
    cands = keyword_search(conn, query, doc_ids, top_k, fts5_available)
    _normalize_scores(cands, "keyword_score", reverse=True)

    # Fill text from DB
    chunk_ids = [c["chunk_id"] for c in cands]
    text_map  = get_chunks_by_ids(conn, chunk_ids)
    for c in cands:
        db_row = text_map.get(c["chunk_id"], {})
        if not c.get("text"):
            c["text"] = db_row.get("text", "")

    results = []
    for c in cands[:top_k]:
        results.append(
            {
                **c,
                "semantic_score": None,
                "final_score":    c["keyword_score"],
            }
        )
    return results


def semantic_only_search(
    conn: sqlite3.Connection,
    model: SentenceTransformer,
    query: str,
    doc_ids: list[int] | None,
    top_k: int,
) -> list[dict]:
    """Semantic-only path: returns normalised results with final_score = semantic_score."""
    cands = semantic_search(model, doc_ids, query, top_k)

    # Fill text from DB
    chunk_ids = [c["chunk_id"] for c in cands]
    text_map  = get_chunks_by_ids(conn, chunk_ids)
    for c in cands:
        db_row = text_map.get(c["chunk_id"], {})
        c["text"] = db_row.get("text", "")

    _normalize_scores(cands, "semantic_score", reverse=False)

    results = []
    for c in cands[:top_k]:
        results.append(
            {
                **c,
                "keyword_score": None,
                "final_score":   c["semantic_score"],
            }
        )
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# G.  INDEX BUILDING
# ═══════════════════════════════════════════════════════════════════════════════
def build_index(
    conn: sqlite3.Connection,
    doc_id: int,
    fts5_available: bool,
    model: SentenceTransformer,
    filename: str,
) -> dict:
    """
    Full index pipeline for one document:
      1. Delete existing chunks + FTS5 entries + FAISS files
      2. Chunk page texts
      3. Insert chunks into SQLite
      4. Insert FTS5 entries
      5. Build FAISS index and save to disk

    Returns a summary dict.
    """
    # ── 1. Clean existing data ───────────────────────────────────────────────
    delete_chunks_for_document(conn, doc_id)
    _delete_faiss_files(doc_id)

    # ── 2. Chunk pages ───────────────────────────────────────────────────────
    pages = get_page_texts(conn, doc_id)
    all_chunk_dicts: list[dict] = []

    for page in pages:
        page_chunks = chunk_page_text(
            doc_id=doc_id,
            filename=filename,
            page_number=page["page_number"],
            text=page["text"],
        )
        all_chunk_dicts.extend(page_chunks)

    if not all_chunk_dicts:
        return {
            "doc_id":        doc_id,
            "chunks_created": 0,
            "faiss_created":  False,
            "fts5_created":   False,
            "error":          "No text chunks could be created from this document.",
        }

    # ── 3. Persist chunks ────────────────────────────────────────────────────
    chunk_ids = insert_chunks(conn, all_chunk_dicts)

    # Build rows with IDs for FTS5 insertion
    chunk_rows = [
        {**d, "id": cid}
        for d, cid in zip(all_chunk_dicts, chunk_ids)
    ]

    # ── 4. FTS5 index ────────────────────────────────────────────────────────
    fts5_created = False
    if fts5_available:
        insert_fts5_entries(conn, chunk_rows)
        fts5_created = True

    # ── 5. FAISS index ───────────────────────────────────────────────────────
    faiss_created = False
    texts = [c["text"] for c in all_chunk_dicts]
    try:
        embeddings = model.encode(texts, convert_to_numpy=True, batch_size=32).astype("float32")
        faiss.normalize_L2(embeddings)

        index = faiss.IndexFlatIP(embeddings.shape[1])
        index.add(embeddings)

        faiss.write_index(index, str(_faiss_path(doc_id)))

        metadata = [
            {
                "chunk_id":    cid,
                "document_id": c["document_id"],
                "filename":    c["filename"],
                "page_number": c["page_number"],
                "chunk_number": c["chunk_number"],
            }
            for c, cid in zip(all_chunk_dicts, chunk_ids)
        ]
        _meta_path(doc_id).write_text(
            json.dumps(metadata, ensure_ascii=False), encoding="utf-8"
        )
        faiss_created = True
    except Exception as exc:
        faiss_created = False

    return {
        "doc_id":         doc_id,
        "chunks_created": len(all_chunk_dicts),
        "faiss_created":  faiss_created,
        "fts5_created":   fts5_created,
        "error":          None,
    }


def _delete_faiss_files(doc_id: int) -> None:
    for path in (_faiss_path(doc_id), _meta_path(doc_id)):
        if path.exists():
            try:
                path.unlink()
            except OSError:
                pass


# ═══════════════════════════════════════════════════════════════════════════════
# H.  KEYWORD HIGHLIGHTING
# ═══════════════════════════════════════════════════════════════════════════════
def highlight_snippet(text: str, query: str, context_chars: int = 200) -> str:
    """
    Return a short substring of *text* that contains the first occurrence of
    any query token, surrounded by ±context_chars of context.
    Falls back to the first context_chars of text if nothing matches.
    """
    if not query.strip():
        return text[:context_chars]

    tokens = [t for t in re.split(r"\s+", query.strip()) if len(t) > 1]
    text_lower = text.lower()

    best_pos = len(text)
    for token in tokens:
        pos = text_lower.find(token.lower())
        if 0 <= pos < best_pos:
            best_pos = pos

    if best_pos == len(text):
        return text[:context_chars] + ("…" if len(text) > context_chars else "")

    start = max(0, best_pos - context_chars // 2)
    end   = min(len(text), best_pos + context_chars // 2)
    snippet = ("…" if start > 0 else "") + text[start:end] + ("…" if end < len(text) else "")
    return snippet


# ═══════════════════════════════════════════════════════════════════════════════
# I.  RELATED PAGES HELPER
# ═══════════════════════════════════════════════════════════════════════════════
def related_pages(page_number: int, page_count: int) -> list[int]:
    """
    Return sorted list of page numbers adjacent to *page_number*.
    Clamps to [1, page_count].  Never includes page 0.
    """
    candidates = {page_number - 1, page_number, page_number + 1}
    return sorted(p for p in candidates if 1 <= p <= page_count)
