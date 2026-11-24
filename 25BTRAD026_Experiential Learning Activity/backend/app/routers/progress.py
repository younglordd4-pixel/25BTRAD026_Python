from __future__ import annotations

from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, select

from ..database import get_db
from ..models import Chunk, Document, Flashcard, StudyLog, utc_now
from ..schemas import ProgressSummaryResponse

router = APIRouter(prefix="/progress", tags=["Progress & Analytics"])


@router.get("/summary", response_model=ProgressSummaryResponse)
def get_progress_summary(db: Session = Depends(get_db)):
    now = utc_now()

    # Documents & chunks
    total_docs = db.scalar(select(func.count(Document.id))) or 0
    total_chunks = db.scalar(select(func.count(Chunk.id))) or 0

    # Flashcards breakdown
    total_cards = db.scalar(select(func.count(Flashcard.id))) or 0
    due_today = db.scalar(select(func.count(Flashcard.id)).where(Flashcard.next_review_at <= now)) or 0
    cards_mastered = db.scalar(select(func.count(Flashcard.id)).where(Flashcard.repetitions >= 3)) or 0
    cards_learning = db.scalar(select(func.count(Flashcard.id)).where((Flashcard.repetitions > 0) & (Flashcard.repetitions < 3))) or 0
    cards_new = db.scalar(select(func.count(Flashcard.id)).where(Flashcard.repetitions == 0)) or 0

    # Total reviews completed
    total_reviews = db.scalar(select(func.count(StudyLog.id))) or 0

    # Retention rate (% of reviews with quality >= 3)
    passing_reviews = db.scalar(select(func.count(StudyLog.id)).where(StudyLog.quality >= 3)) or 0
    retention_rate = (passing_reviews / total_reviews * 100.0) if total_reviews > 0 else 100.0

    # Calculate streak in days
    # Group logs by date
    logs = db.scalars(select(StudyLog.timestamp).order_by(StudyLog.timestamp.desc())).all()
    streak_days = 0
    if logs:
        study_dates = {log_time.date() for log_time in logs}
        today = datetime.now(timezone.utc).date()
        current_check = today

        # If no study today, check if studied yesterday to keep streak alive
        if current_check not in study_dates:
            current_check = today - timedelta(days=1)

        while current_check in study_dates:
            streak_days += 1
            current_check -= timedelta(days=1)

    return ProgressSummaryResponse(
        total_documents=total_docs,
        total_indexed_chunks=total_chunks,
        total_flashcards=total_cards,
        due_today=due_today,
        cards_mastered=cards_mastered,
        cards_learning=cards_learning,
        cards_new=cards_new,
        study_streak_days=streak_days,
        total_reviews_completed=total_reviews,
        retention_rate_percent=round(retention_rate, 1),
    )
