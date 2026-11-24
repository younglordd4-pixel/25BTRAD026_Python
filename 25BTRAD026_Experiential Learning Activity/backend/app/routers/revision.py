from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import FlashcardResponse, ReviewCardRequest, ReviewCardResponse
from ..services.spaced_repetition_service import get_due_flashcards, review_flashcard

router = APIRouter(prefix="/revision", tags=["Spaced Repetition Revision"])


@router.get("/due", response_model=list[FlashcardResponse])
def fetch_due_cards(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Retrieves all flashcards currently due for spaced repetition review."""
    return get_due_flashcards(db, limit=limit)


@router.post("/review/{card_id}", response_model=ReviewCardResponse)
def submit_card_review(
    card_id: int,
    payload: ReviewCardRequest,
    db: Session = Depends(get_db),
):
    """
    Submits a rating (0-5) for a flashcard and recalculates SM-2 interval and easiness factor.
    """
    card = review_flashcard(db, card_id=card_id, quality=payload.quality)
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Flashcard #{card_id} not found.",
        )

    quality_labels = {
        0: "Blackout - Interval reset to 1 day",
        1: "Incorrect - Interval reset to 1 day",
        2: "Hard (Incorrect) - Interval reset to 1 day",
        3: "Passed (Difficult) - Next interval scheduled",
        4: "Good - Interval expanded",
        5: "Easy - Interval maximized",
    }

    return ReviewCardResponse(
        card_id=card.id,
        repetitions=card.repetitions,
        interval=card.interval,
        easiness_factor=card.easiness_factor,
        next_review_at=card.next_review_at,
        quality=payload.quality,
        message=quality_labels.get(payload.quality, "Review recorded successfully"),
    )
