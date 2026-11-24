"""
quiz_engine.py — StudyVerse Offline (Phase B)
==============================================
Deterministic rule-based active recall quiz generator.

Strict Requirements:
- NO LLMs, NO cloud APIs, NO external models.
- Generates exactly 3 questions from retrieved original PDF text.
- Grounded strictly in source PDF sentences.
- Question Types:
    1. Fill in the blank (masked key word with `______`)
    2. Formula / Key-term recall (formula indicator check or definition recall)
    3. True / False (verbatim source statement with source citation)
- Fallback: Manual Recall prompt for noisy/short source text.
"""
from __future__ import annotations

import re
from typing import Any

# Common English stop words to avoid blanking out
STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "if", "because", "as", "until", "while",
    "of", "at", "by", "for", "with", "about", "against", "between", "into", "through",
    "during", "before", "after", "above", "below", "to", "from", "up", "down", "in",
    "out", "on", "off", "over", "under", "again", "further", "then", "once", "here",
    "there", "when", "where", "why", "how", "all", "any", "both", "each", "few", "more",
    "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so",
    "than", "too", "very", "can", "will", "just", "should", "now", "is", "are", "was",
    "were", "be", "been", "being", "have", "has", "had", "having", "do", "does", "did",
    "doing", "this", "that", "these", "those", "it", "its", "they", "them", "their"
}

# Indicators for formula / mathematical relations
FORMULA_INDICATORS = [
    r"=", r"nPr", r"nCr", r"F\s*=\s*ma", r"!", r"\bformula\b", r"\bequals\b",
    r"\bmath\b", r"\bequation\b", r"\+", r"\*", r"/", r"\^", r"\bcalculate\b",
    r"\bsum\b", r"\bproduct\b"
]


def normalize_answer(text: str) -> str:
    """
    Normalize text for flexible answer comparison:
    - Lowercase
    - Collapse extra whitespace
    - Strip surrounding punctuation
    """
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"^[^\w]+|[^\w]+$", "", text)
    return text.strip()


def _split_sentences(text: str) -> list[str]:
    """Split text into clean non-empty sentences."""
    clean = re.sub(r"\s+", " ", text).strip()
    if not clean:
        return []
    # Split on sentence end punctuation followed by space or end of string
    raw_sentences = re.split(r"(?<=[.!?])\s+", clean)
    sentences = []
    for s in raw_sentences:
        s_strip = s.strip()
        if len(s_strip) >= 15:  # Keep meaningful sentences
            sentences.append(s_strip)
    return sentences


def generate_quiz_questions(
    topic: str,
    chunks: list[dict],
    doc_id: int | None = None,
    filename: str = "Document.pdf",
    page_number: int = 1,
) -> list[dict[str, Any]]:
    """
    Generate exactly 3 deterministic rule-based questions from source text chunks.

    Returns a list of 3 question dicts:
        {
            "id": int (1, 2, 3),
            "type": str ("fill_in_blank" | "formula_recall" | "true_false" | "manual_recall"),
            "prompt": str,
            "expected_answer": str,
            "options": list[str] | None,  # for T/F radio buttons
            "is_manual": bool,
            "source_sentence": str,
            "filename": str,
            "page_number": int
        }
    """
    # Combine text from chunks
    combined_text = " ".join([c.get("text", "") for c in chunks if c.get("text")])
    sentences = _split_sentences(combined_text)

    # Use default fallbacks if text is too sparse
    if not sentences:
        return _build_fallback_questions(topic, filename, page_number)

    questions = []

    # ───────────────────────────────────────────────────────────────────────────
    # Question 1: Fill in the blank
    # ───────────────────────────────────────────────────────────────────────────
    q1 = _build_fill_in_blank(sentences[0], filename, page_number)
    if not q1:
        q1 = _build_manual_recall(1, topic, combined_text, filename, page_number)
    questions.append(q1)

    # ───────────────────────────────────────────────────────────────────────────
    # Question 2: Formula / Key-Term Recall
    # ───────────────────────────────────────────────────────────────────────────
    target_sentence = sentences[1] if len(sentences) > 1 else sentences[0]
    q2 = _build_formula_or_key_term(target_sentence, filename, page_number)
    if not q2:
        q2 = _build_manual_recall(2, topic, combined_text, filename, page_number)
    questions.append(q2)

    # ───────────────────────────────────────────────────────────────────────────
    # Question 3: True / False Statement
    # ───────────────────────────────────────────────────────────────────────────
    tf_sentence = sentences[2] if len(sentences) > 2 else sentences[-1]
    q3 = _build_true_false(tf_sentence, filename, page_number)
    if not q3:
        q3 = _build_manual_recall(3, topic, combined_text, filename, page_number)
    questions.append(q3)

    return questions


def _build_fill_in_blank(sentence: str, filename: str, page_number: int) -> dict | None:
    """Build a Fill-in-the-blank question from a sentence."""
    words = re.findall(r"\b[A-Za-z0-9_-]+\b", sentence)
    candidate_words = [
        w for w in words
        if len(w) >= 4 and w.lower() not in STOP_WORDS and not w.isdigit()
    ]
    if not candidate_words:
        return None

    # Pick the longest / most distinct candidate word
    chosen_word = max(candidate_words, key=len)
    pattern = re.compile(rf"\b{re.escape(chosen_word)}\b")
    masked_sentence = pattern.sub("______", sentence, count=1)

    return {
        "id": 1,
        "type": "fill_in_blank",
        "prompt": f"Fill in the missing key term (`______`):\n\n> \"{masked_sentence}\"",
        "expected_answer": chosen_word,
        "options": None,
        "is_manual": False,
        "source_sentence": sentence,
        "filename": filename,
        "page_number": page_number,
    }


def _build_formula_or_key_term(sentence: str, filename: str, page_number: int) -> dict | None:
    """Build a Formula or Key-term recall question."""
    has_formula = any(re.search(pat, sentence, re.IGNORECASE) for pat in FORMULA_INDICATORS)

    if has_formula:
        return {
            "id": 2,
            "type": "formula_recall",
            "prompt": (
                f"State the formula or key relation described in this source sentence:\n\n"
                f"> \"{sentence}\""
            ),
            "expected_answer": sentence,
            "options": None,
            "is_manual": False,
            "source_sentence": sentence,
            "filename": filename,
            "page_number": page_number,
        }

    # Key-term recall definition
    words = re.findall(r"\b[A-Za-z0-9_-]+\b", sentence)
    candidate_words = [
        w for w in words
        if len(w) >= 5 and w.lower() not in STOP_WORDS
    ]
    if candidate_words:
        key_term = candidate_words[0]
        return {
            "id": 2,
            "type": "formula_recall",
            "prompt": (
                f"What key term or concept is referenced in the following definition?\n\n"
                f"> \"{sentence.replace(key_term, '______')}\""
            ),
            "expected_answer": key_term,
            "options": None,
            "is_manual": False,
            "source_sentence": sentence,
            "filename": filename,
            "page_number": page_number,
        }

    return None


def _build_true_false(sentence: str, filename: str, page_number: int) -> dict | None:
    """Build a True/False statement question from source sentence."""
    return {
        "id": 3,
        "type": "true_false",
        "prompt": (
            f"Based on your PDF notes, is the following statement **True** or **False**?\n\n"
            f"> \"{sentence}\""
        ),
        "expected_answer": "True",
        "options": ["True", "False"],
        "is_manual": False,
        "source_sentence": sentence,
        "filename": filename,
        "page_number": page_number,
    }


def _build_manual_recall(
    qid: int, topic: str, text_snippet: str, filename: str, page_number: int
) -> dict:
    """Fallback non-graded active recall question."""
    snippet_preview = text_snippet[:200] + "..." if len(text_snippet) > 200 else text_snippet
    return {
        "id": qid,
        "type": "manual_recall",
        "prompt": (
            f"Explain **{topic}** in your own words based on the source excerpt below:\n\n"
            f"> \"{snippet_preview}\""
        ),
        "expected_answer": "Manual Recall — Self-assessment",
        "options": None,
        "is_manual": True,
        "source_sentence": snippet_preview,
        "filename": filename,
        "page_number": page_number,
    }


def _build_fallback_questions(topic: str, filename: str, page_number: int) -> list[dict]:
    """Generates 3 manual recall questions when text extraction is minimal."""
    return [
        _build_manual_recall(1, topic, f"Core definition of {topic}", filename, page_number),
        _build_manual_recall(2, topic, f"Key formulas and equations for {topic}", filename, page_number),
        _build_manual_recall(3, topic, f"Practical examples of {topic}", filename, page_number),
    ]


def grade_quiz(
    student_answers: dict[int, str], questions: list[dict[str, Any]]
) -> tuple[int, int, list[dict[str, Any]]]:
    """
    Evaluate student answers against generated quiz questions.

    Returns:
    (score, total_auto_graded, detailed_results)
    """
    score = 0
    total_auto_graded = 0
    results = []

    for q in questions:
        qid = q["id"]
        student_ans = student_answers.get(qid, "").strip()
        expected = str(q.get("expected_answer", ""))
        is_manual = q.get("is_manual", False)

        if is_manual:
            is_correct = None
            explanation = "Manual recall prompt. Self-evaluate your response against your notes."
        else:
            total_auto_graded += 1
            norm_student = normalize_answer(student_ans)
            norm_expected = normalize_answer(expected)

            if q["type"] == "true_false":
                is_correct = (norm_student == norm_expected)
            elif q["type"] == "formula_recall" and len(norm_expected) > 25:
                # Substring token match for full formula sentence recall
                tokens = [t for t in norm_expected.split() if len(t) > 3 and t not in STOP_WORDS]
                matches = sum(1 for t in tokens if t in norm_student)
                is_correct = (matches >= max(1, len(tokens) // 2)) or (norm_student in norm_expected)
            else:
                is_correct = (norm_student == norm_expected) or (norm_expected in norm_student and len(norm_student) > 2)

            if is_correct:
                score += 1
                explanation = f"Correct! Matches source sentence: \"{q.get('source_sentence', '')}\""
            else:
                explanation = (
                    f"Expected: **{expected}**. "
                    f"Source sentence: \"{q.get('source_sentence', '')}\""
                )

        results.append(
            {
                "question_id": qid,
                "type": q["type"],
                "prompt": q["prompt"],
                "student_answer": student_ans,
                "expected_answer": expected,
                "is_correct": is_correct,
                "is_manual": is_manual,
                "explanation": explanation,
                "filename": q.get("filename", ""),
                "page_number": q.get("page_number", 1),
            }
        )

    return score, total_auto_graded, results
