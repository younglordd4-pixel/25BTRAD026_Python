from __future__ import annotations

from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_

from ..models import Flashcard, StudyLog, utc_now


def calculate_sm2(
    quality: int,
    current_repetitions: int,
    current_interval: int,
    current_ef: float,
) -> tuple[int, int, float, datetime]:
    """
    Standard SuperMemo-2 (SM-2) algorithm.
    
    Args:
        quality: User performance rating from 0 to 5:
            5 - perfect response
            4 - correct response after hesitation
            3 - correct response recalled with serious difficulty
            2 - incorrect response; where the correct one seemed easy to recall
            1 - incorrect response; the correct one remembered
            0 - complete blackout
        current_repetitions: Number of consecutive successful recalls
        current_interval: Current interval in days
        current_ef: Current easiness factor (minimum 1.3, default 2.5)

    Returns:
        (new_repetitions, new_interval_days, new_ef, next_review_datetime)
    """
    # 1. Update Easiness Factor
    new_ef = current_ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    if new_ef < 1.3:
        new_ef = 1.3

    # 2. Update Repetitions and Interval
    if quality < 3:
        # Failure: reset streak
        new_repetitions = 0
        new_interval = 1
    else:
        # Success
        if current_repetitions == 0:
            new_interval = 1
        elif current_repetitions == 1:
            new_interval = 6
        else:
            new_interval = max(1, round(current_interval * new_ef))
        new_repetitions = current_repetitions + 1

    next_review_at = utc_now() + timedelta(days=new_interval)
    return new_repetitions, new_interval, round(new_ef, 3), next_review_at


def review_flashcard(db: Session, card_id: int, quality: int) -> Flashcard | None:
    """Updates a flashcard using SM-2 and records a StudyLog entry."""
    card = db.get(Flashcard, card_id)
    if not card:
        return None

    now = utc_now()
    new_reps, new_interval, new_ef, next_rev = calculate_sm2(
        quality=quality,
        current_repetitions=card.repetitions,
        current_interval=card.interval,
        current_ef=card.easiness_factor,
    )

    card.repetitions = new_reps
    card.interval = new_interval
    card.easiness_factor = new_ef
    card.next_review_at = next_rev
    card.last_reviewed_at = now
    card.total_reviews += 1
    card.last_quality = quality

    # Record log
    log = StudyLog(
        activity_type="revision",
        card_id=card.id,
        quality=quality,
        score=float(quality) / 5.0,
        timestamp=now,
    )
    db.add(log)
    db.commit()
    db.refresh(card)
    return card


def get_due_flashcards(db: Session, limit: int = 50) -> list[Flashcard]:
    """Returns flashcards due for review up to now, ordered by next_review_at."""
    now = utc_now()
    stmt = (
        select(Flashcard)
        .where(Flashcard.next_review_at <= now)
        .order_by(Flashcard.next_review_at.asc())
        .limit(limit)
    )
    return list(db.scalars(stmt).all())
