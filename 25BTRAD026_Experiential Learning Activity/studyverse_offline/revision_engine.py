"""
revision_engine.py — StudyVerse Offline (Phase B)
==================================================
Simplified SM-2-inspired spaced repetition revision engine.

Rules:
A. Manual Status:
   - Need Revision   → review tomorrow (1 day)
   - Review Tomorrow → review tomorrow (1 day)
   - Understood      → review after 7 days

B. Quiz Recommendation:
   - 0/3 or 1/3 → Need Revision; review tomorrow (1 day)
   - 2/3       → Review Tomorrow; review after 3 days
   - 3/3       → Understood; review after 7 days (or 14/30 days on repeat success)

C. Repeat Success Progression:
   - 1st successful review → 7 days
   - 2nd successful review → 14 days
   - 3rd or further successful review → 30 days maximum
"""
from __future__ import annotations

import sqlite3
from datetime import date, timedelta
from typing import Any

from database import get_revision_topic, upsert_revision_topic


def calculate_next_review(
    action_or_status: str,
    quiz_score: int | None = None,
    quiz_total: int | None = None,
    current_reps: int = 0,
    current_interval: int = 1,
) -> tuple[str, int, int, str]:
    """
    Calculate new revision status, repetition count, interval (days), and next review date string (YYYY-MM-DD).

    Returns:
    (new_status, new_repetitions, new_interval_days, next_review_date_str)
    """
    today = date.today()
    status_clean = action_or_status.lower().strip()

    # If driven by quiz score
    if quiz_score is not None and quiz_total is not None and quiz_total > 0:
        ratio = quiz_score / quiz_total
        if ratio >= 1.0:  # 3/3 or 100%
            new_status = "understood"
            if current_reps == 0:
                new_interval = 7
            elif current_reps == 1:
                new_interval = 14
            else:
                new_interval = 30
            new_reps = current_reps + 1

        elif ratio >= 0.6:  # 2/3 or 66%
            new_status = "review_tomorrow"
            new_interval = 3
            new_reps = max(0, current_reps)

        else:  # 0/3 or 1/3
            new_status = "need_revision"
            new_interval = 1
            new_reps = 0

    else:
        # Driven by manual button click
        if status_clean in ("understood", "marked_understood"):
            new_status = "understood"
            if current_reps == 0:
                new_interval = 7
            elif current_reps == 1:
                new_interval = 14
            else:
                new_interval = 30
            new_reps = current_reps + 1

        elif status_clean in ("review_tomorrow", "tomorrow"):
            new_status = "review_tomorrow"
            new_interval = 1
            new_reps = current_reps

        else:  # "need_revision" or fallback
            new_status = "need_revision"
            new_interval = 1
            new_reps = 0

    next_date = today + timedelta(days=new_interval)
    return new_status, new_reps, new_interval, next_date.isoformat()


def save_topic_revision(
    conn: sqlite3.Connection,
    topic: str,
    doc_id: int | None,
    filename: str,
    page_number: int,
    status_or_action: str,
    quiz_score: int | None = None,
    quiz_total: int | None = None,
) -> dict[str, Any]:
    """
    Save or update a tracked revision topic record in SQLite.
    Computes updated SM-2-inspired parameters.
    """
    existing = get_revision_topic(conn, topic, doc_id, page_number)

    curr_reps = existing["repetitions"] if existing else 0
    curr_interval = existing["interval_days"] if existing else 1

    new_status, new_reps, new_interval, next_date_str = calculate_next_review(
        status_or_action,
        quiz_score=quiz_score,
        quiz_total=quiz_total,
        current_reps=curr_reps,
        current_interval=curr_interval,
    )

    topic_id = upsert_revision_topic(
        conn,
        topic=topic,
        document_id=doc_id,
        source_filename=filename,
        page_number=page_number,
        status=new_status,
        latest_quiz_score=quiz_score,
        latest_quiz_total=quiz_total,
        next_review_date=next_date_str,
        repetitions=new_reps,
        interval_days=new_interval,
    )

    return {
        "id": topic_id,
        "topic": topic,
        "document_id": doc_id,
        "filename": filename,
        "page_number": page_number,
        "status": new_status,
        "next_review_date": next_date_str,
        "interval_days": new_interval,
        "repetitions": new_reps,
    }
