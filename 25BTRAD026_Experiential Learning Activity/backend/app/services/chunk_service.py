from __future__ import annotations
from typing import NamedTuple
from sqlalchemy.orm import Session
from ..models import Chunk, PageText

class ChunkDraft(NamedTuple):
    document_id: int
    page_number: int
    chunk_number: int
    text: str
    character_count: int

CLEAN_BULLETS_PATTERN = [
    (r"[\u2022\u2023\u25E6\u2043\u2219\u2756\u2757\u2758\u2759\u275A\u25AA\u25AB\u25CF\u25CB\uFFFD\u200B]", " "),
    (r"\s+", " "),
]


def clean_chunk_text(text: str) -> str:
    """Cleans OCR artifacts, bullet symbols, and collapses whitespace."""
    s = text
    import re
    for pat, rep in CLEAN_BULLETS_PATTERN:
        s = re.sub(pat, rep, s)
    return s.strip()


def create_chunk_drafts_for_document(db: Session, document_id: int) -> list[ChunkDraft]:
    """
    Processes PageText records into clean chunks using sentence-aware boundary matching.
    Window: ~650 chars, Overlap: ~130 chars, Minimum length: 150 chars.
    """
    pages = db.query(PageText).filter(PageText.document_id == document_id).order_by(PageText.page_number).all()
    all_drafts: list[ChunkDraft] = []
    
    for page in pages:
        if not page.text:
            continue
        page_drafts = chunk_page_text(document_id, page.page_number, page.text)
        all_drafts.extend(page_drafts)
                
    return all_drafts

def save_chunks(db: Session, drafts: list[ChunkDraft]) -> list[Chunk]:
    """Persists ChunkDrafts to the database."""
    chunks = [
        Chunk(
            document_id=d.document_id,
            page_number=d.page_number,
            chunk_number=d.chunk_number,
            text=d.text,
            character_count=d.character_count
        ) for d in drafts
    ]
    db.add_all(chunks)
    db.flush()
    return chunks

def get_chunk_preview(text: str, length: int = 250) -> str:
    """Helper for debug output."""
    return text[:length] + "..." if len(text) > length else text


def chunk_page_text(document_id: int, page_number: int, text: str) -> list[ChunkDraft]:
    """Chunks text from a single page into clean, sentence-aware ChunkDrafts."""
    if not text:
        return []
    normalized_text = clean_chunk_text(text)
    text_len = len(normalized_text)
    drafts: list[ChunkDraft] = []
    start = 0
    chunk_count = 0
    
    # Target chunk size: ~650 chars, with ~130 chars overlap
    target_size = 650
    overlap = 130
    
    while start < text_len:
        end = min(start + target_size, text_len)
        chunk_text = normalized_text[start:end]
        
        # If not at the end of the text, look for a natural sentence break (. ! ? or colon/newline)
        if end < text_len:
            search_window = normalized_text[max(start, end - 120):end]
            # Priority 1: sentence terminators followed by space
            sentence_breaks = [i for i, c in enumerate(search_window) if c in ".!?" and (i + 1 == len(search_window) or search_window[i + 1:i + 2].isspace())]
            if sentence_breaks:
                best_break = max(sentence_breaks)
                end = max(start, (end - 120) + best_break + 1)
                chunk_text = normalized_text[start:end].strip()
            else:
                # Priority 2: whitespace boundary so words aren't cut in half
                space_breaks = [i for i, c in enumerate(search_window) if c.isspace()]
                if space_breaks:
                    best_break = max(space_breaks)
                    end = max(start, (end - 120) + best_break + 1)
                    chunk_text = normalized_text[start:end].strip()
        
        chunk_text = chunk_text.strip()
        if len(chunk_text) >= 150:
            chunk_count += 1
            drafts.append(ChunkDraft(
                document_id=document_id,
                page_number=page_number,
                chunk_number=chunk_count,
                text=chunk_text,
                character_count=len(chunk_text),
            ))
        elif chunk_count == 0 and len(normalized_text) >= 30 and not drafts:
            chunk_count += 1
            drafts.append(ChunkDraft(
                document_id=document_id,
                page_number=page_number,
                chunk_number=chunk_count,
                text=normalized_text,
                character_count=len(normalized_text),
            ))
            break
            
        step = max(end - start - overlap, 200)
        start += step
        if start >= text_len:
            break
            
    return drafts
