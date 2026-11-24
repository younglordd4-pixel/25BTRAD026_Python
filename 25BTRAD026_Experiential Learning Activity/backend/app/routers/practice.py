from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..database import get_db
from ..models import Document, Flashcard
from ..schemas import (
    FlashcardCreate,
    FlashcardResponse,
    GenerateFlashcardsRequest,
    GenerateFlashcardsResponse,
)
from ..services.quiz_service import generate_flashcards_for_document

router = APIRouter(prefix="/practice", tags=["Practice Arena"])


@router.get("/flashcards", response_model=list[FlashcardResponse])
def list_flashcards(
    document_id: int | None = Query(None, description="Optional document ID filter"),
    db: Session = Depends(get_db),
):
    stmt = select(Flashcard)
    if document_id is not None:
        stmt = stmt.where(Flashcard.document_id == document_id)
    stmt = stmt.order_by(Flashcard.id.desc())
    return list(db.scalars(stmt).all())


@router.post("/generate", response_model=GenerateFlashcardsResponse)
def generate_cards(
    payload: GenerateFlashcardsRequest,
    db: Session = Depends(get_db),
):
    doc_ids = payload.document_ids
    if not doc_ids:
        # If no documents specified, generate for all documents with extractable text
        docs = db.scalars(select(Document).where(Document.has_extractable_text == True)).all()
        doc_ids = [d.id for d in docs]

    if not doc_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No eligible documents found. Please upload and index a PDF first.",
        )

    all_generated: list[Flashcard] = []
    for doc_id in doc_ids:
        cards = generate_flashcards_for_document(db, doc_id, max_cards=payload.max_cards_per_doc)
        all_generated.extend(cards)

    return GenerateFlashcardsResponse(
        total_generated=len(all_generated),
        cards=all_generated,
        message=f"Generated {len(all_generated)} new practice cards.",
    )


@router.post("/create", response_model=FlashcardResponse, status_code=status.HTTP_201_CREATED)
def create_flashcard(
    payload: FlashcardCreate,
    db: Session = Depends(get_db),
):
    doc = db.get(Document, payload.document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    card = Flashcard(
        document_id=payload.document_id,
        question=payload.question,
        answer=payload.answer,
        context=payload.context,
        page_number=payload.page_number,
    )
    db.add(card)
    db.commit()
    db.refresh(card)
    return card


@router.delete("/flashcards/{card_id}", status_code=status.HTTP_200_OK)
def delete_flashcard(card_id: int, db: Session = Depends(get_db)):
    card = db.get(Flashcard, card_id)
    if not card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flashcard not found")
    db.delete(card)
    db.commit()
    return {"message": "Flashcard deleted successfully", "card_id": card_id}
