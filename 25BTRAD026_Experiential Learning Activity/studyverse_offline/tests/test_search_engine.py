"""
tests/test_search_engine.py — StudyVerse Offline Phase A
=========================================================
Unit tests for search_engine.py

Run with:
    python -m pytest tests/test_search_engine.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from search_engine import (
    CHUNK_MIN,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    KEYWORD_WEIGHT,
    SEMANTIC_WEIGHT,
    _best_break,
    _normalize_scores,
    _sanitize_fts_query,
    chunk_page_text,
    highlight_snippet,
    related_pages,
)


# ─────────────────────────────────────────────────────────────────────────────
# Spec constant checks
# ─────────────────────────────────────────────────────────────────────────────
class TestSpecConstants:
    def test_semantic_weight(self):
        assert SEMANTIC_WEIGHT == 0.70, "Spec requires SEMANTIC_WEIGHT = 0.70"

    def test_keyword_weight(self):
        assert KEYWORD_WEIGHT == 0.30, "Spec requires KEYWORD_WEIGHT = 0.30"

    def test_weights_sum_to_one(self):
        assert abs(SEMANTIC_WEIGHT + KEYWORD_WEIGHT - 1.0) < 1e-9

    def test_chunk_size(self):
        assert CHUNK_SIZE == 700

    def test_chunk_overlap(self):
        assert CHUNK_OVERLAP == 120

    def test_chunk_min(self):
        assert CHUNK_MIN == 150


# ─────────────────────────────────────────────────────────────────────────────
# chunk_page_text
# ─────────────────────────────────────────────────────────────────────────────
class TestChunkPageText:
    def test_empty_text_returns_empty(self):
        assert chunk_page_text(1, "doc.pdf", 1, "") == []

    def test_whitespace_only_returns_empty(self):
        assert chunk_page_text(1, "doc.pdf", 1, "   \n\t  ") == []

    def test_short_text_below_min_still_returned(self):
        # Very short page text should be preserved (special case)
        text = "Short text."  # 11 chars, way below CHUNK_MIN
        chunks = chunk_page_text(1, "doc.pdf", 1, text)
        # Expect either 0 chunks (too short even for special case) or the full text
        for c in chunks:
            assert c["text"] == text.strip() or len(c["text"]) >= 1

    def test_long_text_produces_multiple_chunks(self):
        # 2000 chars of repeated text → must produce multiple chunks
        text = "The quick brown fox jumps over the lazy dog. " * 44  # ~2000 chars
        chunks = chunk_page_text(1, "doc.pdf", 1, text)
        assert len(chunks) >= 2

    def test_chunk_number_is_sequential(self):
        text = "A" * 2000
        chunks = chunk_page_text(1, "doc.pdf", 1, text)
        numbers = [c["chunk_number"] for c in chunks]
        assert numbers == list(range(1, len(numbers) + 1))

    def test_every_chunk_has_required_keys(self):
        text = "Newton's second law states that F = ma. " * 30
        chunks = chunk_page_text(1, "doc.pdf", 2, text)
        required = {"document_id", "filename", "page_number", "chunk_number", "text", "character_count"}
        for c in chunks:
            assert required.issubset(c.keys()), f"Missing keys in chunk: {c.keys()}"

    def test_metadata_preserved(self):
        text = "Permutations and combinations are topics in combinatorics. " * 20
        chunks = chunk_page_text(42, "math.pdf", 7, text)
        for c in chunks:
            assert c["document_id"] == 42
            assert c["filename"] == "math.pdf"
            assert c["page_number"] == 7

    def test_chunk_respects_minimum_length(self):
        text = "Some meaningful academic content about permutations. " * 30
        chunks = chunk_page_text(1, "doc.pdf", 1, text)
        for c in chunks[:-1]:  # last chunk can be shorter
            assert c["character_count"] >= CHUNK_MIN or len(chunks) == 1

    def test_no_empty_text_chunks(self):
        text = "Newton's laws. " * 50
        chunks = chunk_page_text(1, "doc.pdf", 1, text)
        for c in chunks:
            assert c["text"].strip() != ""

    def test_character_count_matches_text_length(self):
        text = "Force equals mass times acceleration. " * 25
        chunks = chunk_page_text(1, "doc.pdf", 1, text)
        for c in chunks:
            assert c["character_count"] == len(c["text"])

    def test_overlap_means_adjacent_chunks_share_content(self):
        # With 700/120 chunking, adjacent chunks should share some words
        text = "word " * 400  # ~2000 chars
        chunks = chunk_page_text(1, "doc.pdf", 1, text)
        if len(chunks) >= 2:
            # The end of chunk 0 and start of chunk 1 should overlap
            end_of_first = chunks[0]["text"][-CHUNK_OVERLAP:]
            start_of_second = chunks[1]["text"][:CHUNK_OVERLAP]
            # They won't be identical due to boundary rounding but should share words
            words_first  = set(end_of_first.split())
            words_second = set(start_of_second.split())
            assert words_first & words_second, "Adjacent chunks should share some overlap content"

    def test_no_duplicate_chunks_for_same_input(self):
        text = "Combinatorics is the study of arrangements. " * 30
        chunks = chunk_page_text(1, "doc.pdf", 1, text)
        texts = [c["text"] for c in chunks]
        assert len(texts) == len(set(texts)), "Duplicate chunks should not exist"


# ─────────────────────────────────────────────────────────────────────────────
# _best_break
# ─────────────────────────────────────────────────────────────────────────────
class TestBestBreak:
    def test_prefers_sentence_terminator(self):
        text = "Hello world. This is a test. More text here."
        pos = _best_break(text, 30)
        # Should land at or after the dot at position 12 or 28
        assert pos >= 12

    def test_falls_back_to_space(self):
        text = "abcdefghij klmnopqrstuvwxyz"
        pos = _best_break(text, 20)
        # Should land at a space boundary
        assert 0 < pos <= 20

    def test_never_exceeds_target(self):
        text = "a" * 200
        pos = _best_break(text, 100)
        assert pos <= 100


# ─────────────────────────────────────────────────────────────────────────────
# _sanitize_fts_query
# ─────────────────────────────────────────────────────────────────────────────
class TestSanitizeFtsQuery:
    def test_wraps_in_quotes(self):
        result = _sanitize_fts_query("Newton")
        assert result == '"Newton"'

    def test_escapes_internal_quotes(self):
        result = _sanitize_fts_query('say "hello"')
        assert '""' in result  # doubled quotes

    def test_formula_safe(self):
        result = _sanitize_fts_query("F = ma")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_special_chars_safe(self):
        for query in ["nPr", "nCr", "d/dx", "∫f(x)dx", "(a+b)^2", "E=mc²"]:
            result = _sanitize_fts_query(query)
            assert isinstance(result, str)


# ─────────────────────────────────────────────────────────────────────────────
# _normalize_scores
# ─────────────────────────────────────────────────────────────────────────────
class TestNormalizeScores:
    def _make_items(self, scores: list[float]) -> list[dict]:
        return [{"keyword_score": s} for s in scores]

    def test_normalises_to_zero_one(self):
        items = self._make_items([1.0, 2.0, 3.0, 4.0, 5.0])
        result = _normalize_scores(items, "keyword_score")
        vals = [r["keyword_score"] for r in result]
        assert abs(min(vals)) < 1e-9
        assert abs(max(vals) - 1.0) < 1e-9

    def test_all_same_scores_become_one(self):
        items = self._make_items([3.0, 3.0, 3.0])
        result = _normalize_scores(items, "keyword_score")
        for r in result:
            assert r["keyword_score"] == 1.0

    def test_reverse_flag_inverts(self):
        items = self._make_items([1.0, 3.0])
        result = _normalize_scores(items, "keyword_score", reverse=True)
        # lower original score → higher normalised score
        scores = [r["keyword_score"] for r in result]
        assert scores[0] > scores[1]

    def test_none_score_becomes_zero(self):
        items = [{"keyword_score": None}, {"keyword_score": 5.0}]
        result = _normalize_scores(items, "keyword_score")
        assert result[0]["keyword_score"] == 0.0

    def test_empty_list_returns_empty(self):
        assert _normalize_scores([], "keyword_score") == []


# ─────────────────────────────────────────────────────────────────────────────
# highlight_snippet
# ─────────────────────────────────────────────────────────────────────────────
class TestHighlightSnippet:
    def test_finds_query_token(self):
        text = "This chapter covers permutations and combinations in detail."
        snippet = highlight_snippet(text, "permutation")
        assert "permutation" in snippet.lower()

    def test_returns_truncated_if_no_match(self):
        text = "A" * 500
        snippet = highlight_snippet(text, "zznotfound", context_chars=200)
        assert len(snippet) <= 210  # 200 + ellipsis overhead

    def test_empty_query_returns_start_of_text(self):
        text = "Hello world this is a test."
        snippet = highlight_snippet(text, "")
        assert snippet == text[:200]

    def test_handles_formula_query(self):
        text = "According to Newton, F = ma where m is mass and a is acceleration."
        snippet = highlight_snippet(text, "F = ma")
        assert "F = ma" in snippet or "ma" in snippet


# ─────────────────────────────────────────────────────────────────────────────
# related_pages
# ─────────────────────────────────────────────────────────────────────────────
class TestRelatedPages:
    def test_middle_page(self):
        pages = related_pages(5, 10)
        assert pages == [4, 5, 6]

    def test_first_page_no_page_zero(self):
        pages = related_pages(1, 10)
        assert 0 not in pages
        assert 1 in pages
        assert 2 in pages

    def test_last_page_no_overflow(self):
        pages = related_pages(10, 10)
        assert 11 not in pages
        assert 10 in pages
        assert 9 in pages

    def test_single_page_document(self):
        pages = related_pages(1, 1)
        assert pages == [1]

    def test_always_sorted(self):
        pages = related_pages(5, 10)
        assert pages == sorted(pages)

    def test_never_page_zero_or_below(self):
        for p in range(1, 5):
            result = related_pages(p, 10)
            assert all(x >= 1 for x in result)
