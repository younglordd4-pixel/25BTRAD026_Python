from __future__ import annotations

from datetime import datetime

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class HealthResponse(BaseModel):
    status: str
    app: str


class PageTextResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    page_number: int
    character_count: int
    text: str | None


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    page_count: int
    has_extractable_text: bool
    extraction_status: str
    extraction_message: str | None
    uploaded_at: datetime
    extracted_page_count: int
    is_indexed: bool = False
    chunks_count: int = 0
    faiss_index_exists: bool = False
    metadata_exists: bool = False


class DocumentDetailResponse(DocumentResponse):
    pass


class DeleteDocumentResponse(BaseModel):
    message: str
    document_id: int
    cleanup_complete: bool = False
    cleanup_errors: list[str] = Field(default_factory=list)
    file_deleted: bool
    chunks_deleted: bool = False
    keyword_entries_deleted: bool = False
    faiss_index_deleted: bool = False
    metadata_deleted: bool = False


class IndexDocumentResponse(BaseModel):
    document_id: int
    filename: str
    status: str
    pages_with_text: int
    chunks_created: int
    faiss_index_created: bool
    keyword_index_created: bool
    message: str


class IndexAllResponse(BaseModel):
    results: list[IndexDocumentResponse]
    indexed_document_count: int
    failed_or_warning_count: int
    total_chunks_created: int


SearchMode = Literal["semantic", "keyword", "hybrid"]


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, examples=["What is permutation?"])
    document_ids: list[int] = Field(default_factory=list)
    mode: SearchMode = "hybrid"
    top_k: int = Field(default=5, ge=1, le=10)
    min_score: float = Field(default=0.0, ge=0.0, le=1.0)
    include_debug: bool = False

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Query cannot be blank or only whitespace.")
        return v.strip()


class SearchResultResponse(BaseModel):
    rank: int
    chunk_id: int
    document_id: int
    filename: str
    page_number: int
    chunk_number: int
    text: str
    snippet: str
    semantic_score: float | None = None
    semantic_score_percent: float | None = None
    keyword_score: float | None = None
    keyword_score_percent: float | None = None
    final_score: float
    final_score_percent: float
    matched_by: SearchMode
    related_pages: list[int]


class DirectAnswerResponse(BaseModel):
    direct_answer: str
    key_points: list[str] = Field(default_factory=list)
    confidence: str = "medium"
    primary_source_page: int | None = None
    primary_source_filename: str | None = None


class SearchResponse(BaseModel):
    query: str
    mode: SearchMode
    total_candidates: int
    returned_results: int
    results: list[SearchResultResponse]
    message: str
    filtered_by_min_score: bool = False
    direct_answer: DirectAnswerResponse | None = None
    debug: dict[str, Any] | None = None


class ChunkPreviewResponse(BaseModel):
    source_filename: str
    page_number: int
    chunk_number: int
    preview: str


class DocumentDebugResponse(BaseModel):
    document_id: int
    filename: str
    page_count: int
    page_text_count: int
    chunks_count: int
    faiss_index_exists: bool
    metadata_exists: bool
    fts5_entries_count: int
    first_chunk_previews: list[ChunkPreviewResponse]


# ── Spaced Repetition & Practice Schemas ─────────────────────────────────────
class FlashcardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: int
    chunk_id: int | None = None
    question: str
    answer: str
    context: str
    page_number: int
    repetitions: int
    interval: int
    easiness_factor: float
    next_review_at: datetime
    last_reviewed_at: datetime | None = None
    total_reviews: int
    last_quality: int | None = None
    created_at: datetime


class FlashcardCreate(BaseModel):
    document_id: int
    question: str
    answer: str
    context: str = ""
    page_number: int = 1


class GenerateFlashcardsRequest(BaseModel):
    document_ids: list[int] = Field(default_factory=list)
    max_cards_per_doc: int = Field(default=10, ge=1, le=50)


class GenerateFlashcardsResponse(BaseModel):
    total_generated: int
    cards: list[FlashcardResponse]
    message: str


class ReviewCardRequest(BaseModel):
    quality: int = Field(..., ge=0, le=5, description="SM-2 quality rating: 0=blackout, 1=wrong, 2=hard wrong, 3=hard right, 4=good, 5=easy")


class ReviewCardResponse(BaseModel):
    card_id: int
    repetitions: int
    interval: int
    easiness_factor: float
    next_review_at: datetime
    quality: int
    message: str


class ProgressSummaryResponse(BaseModel):
    total_documents: int
    total_indexed_chunks: int
    total_flashcards: int
    due_today: int
    cards_mastered: int  # repetitions >= 3
    cards_learning: int  # repetitions < 3 and repetitions > 0
    cards_new: int       # repetitions == 0
    study_streak_days: int
    total_reviews_completed: int
    retention_rate_percent: float
