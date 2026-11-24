from __future__ import annotations

from app.services.chunk_service import chunk_page_text
from app.services.search_service import related_pages


def test_chunks_are_non_empty_preserve_page_and_order():
    text = " ".join([f"Sentence {index} explains permutation order." for index in range(80)])
    chunks = chunk_page_text(document_id=1, page_number=3, text=text)
    assert chunks
    assert all(chunk.text.strip() for chunk in chunks)
    assert all(chunk.character_count >= 150 for chunk in chunks)
    assert all(chunk.page_number == 3 for chunk in chunks)
    assert [chunk.chunk_number for chunk in chunks] == list(range(1, len(chunks) + 1))


def test_chunking_is_deterministic_and_overlap_is_reasonable():
    text = " ".join([f"Permutation means arrangement where order matters {index}." for index in range(100)])
    first = chunk_page_text(1, 1, text)
    second = chunk_page_text(1, 1, text)
    assert [chunk.text for chunk in first] == [chunk.text for chunk in second]
    assert len(first) > 1
    overlap_words = set(first[0].text[-140:].split())
    next_words = set(first[1].text[:180].split())
    assert overlap_words.intersection(next_words)


def test_related_pages_are_always_valid():
    assert related_pages(1, 1) == [1]
    assert related_pages(1, 3) == [1, 2]
    assert related_pages(2, 3) == [1, 2, 3]
    assert related_pages(3, 3) == [2, 3]
