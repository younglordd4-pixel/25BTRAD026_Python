from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    page_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    extracted_page_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    has_extractable_text: Mapped[bool] = mapped_column(nullable=False, default=False)
    extraction_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    extraction_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    deletion_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    deletion_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    pages: Mapped[list["PageText"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="PageText.page_number",
    )
    chunks: Mapped[list["Chunk"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="Chunk.page_number, Chunk.chunk_number",
    )


class PageText(Base):
    __tablename__ = "page_text"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    character_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    document: Mapped[Document] = relationship(back_populates="pages")


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    chunk_number: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    character_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    document: Mapped[Document] = relationship(back_populates="chunks")


class Flashcard(Base):
    __tablename__ = "flashcards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_id: Mapped[int | None] = mapped_column(ForeignKey("chunks.id", ondelete="SET NULL"), nullable=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[str] = mapped_column(Text, nullable=False, default="")
    page_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    
    # SM-2 Spaced Repetition parameters
    repetitions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    interval: Mapped[int] = mapped_column(Integer, nullable=False, default=1)  # interval in days
    easiness_factor: Mapped[float] = mapped_column(Float, nullable=False, default=2.5)
    next_review_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_reviews: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_quality: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    document: Mapped[Document] = relationship()


class StudyLog(Base):
    __tablename__ = "study_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    activity_type: Mapped[str] = mapped_column(String(64), nullable=False)  # "quiz", "revision", "search", "upload"
    card_id: Mapped[int | None] = mapped_column(ForeignKey("flashcards.id", ondelete="SET NULL"), nullable=True)
    quality: Mapped[int | None] = mapped_column(Integer, nullable=True)  # SM-2 score 0-5
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
