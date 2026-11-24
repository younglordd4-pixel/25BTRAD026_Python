from __future__ import annotations

from app.services.answer_service import (
    extract_query_concept,
    find_definition_sentence,
    generate_direct_answer,
    clean_raw_text,
)


def test_extract_query_concept():
    assert extract_query_concept("Define an operating system") == "operating system"
    assert extract_query_concept("What is a deadlock?") == "deadlock"
    assert extract_query_concept("Explain virtual memory in detail") == "virtual memory"
    assert extract_query_concept("Meaning of thrashing") == "thrashing"


def test_find_definition_sentence_exact_and_acronym():
    text = (
        "OPERATING SYSTEM: An OS is defined as a System program that controls the execution "
        "of application programs and acts as an interface between applications and the computer hardware. "
        "It provides convenience and efficiency."
    )
    defn = find_definition_sentence("operating system", text)
    assert defn is not None
    assert "defined as a System program" in defn


def test_generate_direct_answer_returns_high_confidence_and_points():
    chunks = [
        {
            "text": (
                "An operating system is defined as a system software that manages computer hardware. "
                "The primary goal of an operating system is convenience for the user. "
                "It provides an efficient execution environment."
            ),
            "page_number": 5,
            "filename": "os_intro.pdf",
            "score": 0.95,
        }
    ]
    res = generate_direct_answer("Define an operating system", chunks)
    assert res.confidence == "high"
    assert "system software that manages computer hardware" in res.direct_answer
    assert res.primary_source_page == 5
    assert len(res.key_points) >= 1


def test_clean_raw_text_strips_unicode_bullets():
    dirty = "Features:\u2756 High efficiency \u2022 Low latency   \u25CF Robust"
    cleaned = clean_raw_text(dirty)
    assert "\u2756" not in cleaned
    assert "\u2022" not in cleaned
    assert "\u25CF" not in cleaned
    assert "High efficiency Low latency Robust" in cleaned
