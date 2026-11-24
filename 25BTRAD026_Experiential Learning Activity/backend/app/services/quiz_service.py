from __future__ import annotations

import re
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..models import Chunk, Document, Flashcard, utc_now


DEFINITION_PATTERNS = [
    re.compile(r"([A-Z][A-Za-z0-9\s\-]{2,40})\s+(?:is defined as|is called|refers to|means|is an?)\s+([^.?!;\n]{15,250})[.?!]", re.IGNORECASE),
    re.compile(r"([A-Z][A-Za-z0-9\s\-]{2,40})\s*:\s*([^.?!;\n]{15,250})[.?!]", re.IGNORECASE),
    re.compile(r"(?:The\s+)?formula\s+for\s+([A-Za-z0-9\s\-]{2,35})\s+is\s+([^.?!;\n]{5,150})[.?!]", re.IGNORECASE),
    re.compile(r"([A-Z][A-Za-z0-9\s\-]{2,35})\s+states\s+that\s+([^.?!;\n]{15,250})[.?!]", re.IGNORECASE),
]


def extract_cards_from_chunk(chunk: Chunk) -> list[tuple[str, str, str]]:
    """
    Extracts candidate (question, answer, context) tuples from a chunk of text.
    Uses regex patterns to identify definitions, laws, principles, and formulas.
    """
    results: list[tuple[str, str, str]] = []
    text = chunk.text

    for pattern in DEFINITION_PATTERNS:
        for match in pattern.finditer(text):
            concept = match.group(1).strip()
            explanation = match.group(2).strip()

            # Clean up concept
            concept_clean = re.sub(r"^(A|An|The)\s+", "", concept, flags=re.IGNORECASE).strip()
            if len(concept_clean) < 3 or len(explanation) < 10:
                continue

            question = f"What is {concept_clean}?"
            answer = f"{concept} is {explanation}."
            results.append((question, answer, text[:400]))

    # Fallback: if no pattern matched, generate a conceptual summary question from the first sentence
    if not results:
        sentences = [s.strip() for s in re.split(r"[.?!]\s+", text) if len(s.strip()) > 30]
        if sentences:
            lead = sentences[0]
            # Try to grab topic from the first few words
            words = lead.split()
            topic = " ".join(words[:4])
            results.append((
                f"Explain the key concept in: '{topic}...'",
                lead,
                text[:400],
            ))

    return results


def generate_flashcards_for_document(db: Session, document_id: int, max_cards: int = 10) -> list[Flashcard]:
    """Generates flashcards from a document's chunks and persists them."""
    doc = db.get(Document, document_id)
    if not doc:
        return []

    # Get chunks for document
    chunks = db.query(Chunk).filter(Chunk.document_id == document_id).order_by(Chunk.page_number, Chunk.chunk_number).all()
    if not chunks:
        return []

    created_cards: list[Flashcard] = []
    seen_questions: set[str] = set()

    # Load existing questions to prevent duplicates
    existing = db.scalars(select(Flashcard.question).where(Flashcard.document_id == document_id)).all()
    seen_questions.update(q.lower() for q in existing)

    for chunk in chunks:
        if len(created_cards) >= max_cards:
            break

        candidates = extract_cards_from_chunk(chunk)
        for question, answer, context in candidates:
            q_key = question.lower()
            if q_key in seen_questions:
                continue

            seen_questions.add(q_key)
            card = Flashcard(
                document_id=document_id,
                chunk_id=chunk.id,
                question=question,
                answer=answer,
                context=context,
                page_number=chunk.page_number,
                repetitions=0,
                interval=1,
                easiness_factor=2.5,
                next_review_at=utc_now(),
                created_at=utc_now(),
            )
            created_cards.append(card)
            if len(created_cards) >= max_cards:
                break

    if created_cards:
        db.add_all(created_cards)
        db.commit()
        for c in created_cards:
            db.refresh(c)

    return created_cards
