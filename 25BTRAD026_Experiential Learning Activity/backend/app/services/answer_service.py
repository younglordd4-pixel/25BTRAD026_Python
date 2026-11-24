"""
Answer Generation Service
=========================
Generates clean, direct, and concise answers to user study queries from
retrieved context chunks.

Features:
  • Extracts direct definitions when answering "define / what is / explain X" questions.
  • Synthesizes bulleted explanations when asked about features/types/objectives.
  • Cleans messy formatting (orphan punctuation, broken headers, weird OCR tokens).
  • Fallback to highest-relevance salient sentence extraction.
"""
from __future__ import annotations

import re
from typing import NamedTuple


class GeneratedAnswer(NamedTuple):
    direct_answer: str
    key_points: list[str]
    confidence: str  # "high", "medium", "low"
    primary_source_page: int | None
    primary_source_filename: str | None


# Stop words that don't help identify core concept keywords
QUERY_NOISE_WORDS = {
    "what", "is", "an", "a", "the", "define", "explain", "describe",
    "meaning", "of", "definition", "concept", "state", "how", "does", "work",
    "tell", "me", "about", "give", "brief"
}

CLEAN_SUB_PATTERNS = [
    (re.compile(r"[\u2022\u2023\u25E6\u2043\u2219\u2756\u2757\u2758\u2759\u275A\u25AA\u25AB\u25CF\u25CB\uFFFD\u200B]"), " "),
    (re.compile(r"\s+"), " "),
]


def clean_raw_text(text: str) -> str:
    """Removes messy OCR bullet marks, control chars, and normalizes spacing."""
    s = text
    for pat, rep in CLEAN_SUB_PATTERNS:
        s = pat.sub(rep, s)
    return s.strip()


def extract_query_concept(query: str) -> str:
    """Extracts the primary target term/phrase from a definition question."""
    q = query.strip().rstrip("?.!")
    # Look for patterns like "define X", "what is X", "explain X"
    m = re.search(r"^(?:what\s+is|what\s+are|define|explain|describe|meaning\s+of)\s+(?:an?|the)?\s*(.+)$", q, re.IGNORECASE)
    if m:
        target = m.group(1).strip()
        # Remove trailing words like "in operating system", "with examples"
        target = re.sub(r"\s+(?:in\s+detail|briefly|with\s+examples?|in\s+short)$", "", target, flags=re.IGNORECASE)
        return target
    # Fallback: remove query noise words
    words = [w for w in q.split() if w.lower() not in QUERY_NOISE_WORDS]
    return " ".join(words) if words else q


def split_sentences(text: str) -> list[str]:
    """Splits text into clean, well-formed sentences."""
    # Handle common abbreviations so they don't break sentences
    cleaned = clean_raw_text(text)
    raw_sents = re.split(r"(?<=[.?!])\s+(?=[A-Z0-9])", cleaned)
    sents = []
    for s in raw_sents:
        s = s.strip()
        if len(s) >= 15:
            sents.append(s)
    return sents


def find_definition_sentence(concept: str, text: str) -> str | None:
    """
    Searches for an authoritative definition matching the requested concept.
    Recognizes patterns such as:
      - '<Concept> is defined as ...'
      - '<Concept> is a/an ... that ...'
      - '<Concept> refers to ...'
      - '<Concept> acts as ...'
    """
    if not concept:
        return None

    # Clean concept words for regex matching
    escaped_concept = re.escape(concept.strip())
    # Match full term, or primary nouns if concept is multi-word
    words = [re.escape(w) for w in concept.split() if len(w) > 2]
    
    # Generate acronym if multi-word (e.g. "operating system" -> "OS")
    acronym_list = []
    tokens = [t for t in concept.split() if t.lower() not in QUERY_NOISE_WORDS]
    if len(tokens) >= 2:
        acr = "".join(t[0].upper() for t in tokens)
        acronym_list.append(re.escape(acr))
    elif len(concept) <= 5 and concept.isupper():
        acronym_list.append(re.escape(concept))
        
    all_terms = [escaped_concept] + words + acronym_list
    concept_regex = rf"(?:{'|'.join(dict.fromkeys(all_terms))})"

    patterns = [
        # "An OS is defined as..."
        rf"(?:[A-Z][A-Za-z0-9\s,-]{{0,25}}\s+)?(?:{concept_regex})\s+(?:is|are)\s+defined\s+as\s+([^.?!;]{{20,350}}[.?])",
        # "An operating system is a program that controls..."
        rf"(?:[A-Z][A-Za-z0-9\s,-]{{0,25}}\s+)?(?:{concept_regex})\s+(?:is|are)\s+(?:an?|the)\s+([^.?!;]{{20,350}}[.?])",
        # "An operating system acts as / controls..."
        rf"(?:[A-Z][A-Za-z0-9\s,-]{{0,25}}\s+)?(?:{concept_regex})\s+(?:acts\s+as|refers\s+to|functions\s+as|serves\s+as)\s+([^.?!;]{{20,350}}[.?])",
        # "OPERATING SYSTEM: An OS is ..."
        rf"(?:{concept_regex})\s*:\s*([^.?!;]{{20,350}}[.?])",
    ]

    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            full_match = m.group(0).strip()
            # Trim leading section headers like 'OPERATING SYSTEM OVERVIEW: ' or 'CHAPTER 1: '
            header_split = re.split(r":\s+", full_match, maxsplit=1)
            if len(header_split) == 2 and len(header_split[1]) >= 25:
                full_match = header_split[1].strip()
            return full_match

    return None


def generate_direct_answer(query: str, retrieved_chunks: list[dict]) -> GeneratedAnswer:
    """
    Synthesizes a clean, direct answer from retrieved search candidate chunks.
    """
    if not retrieved_chunks:
        return GeneratedAnswer(
            direct_answer="No relevant information was found in your indexed documents.",
            key_points=[],
            confidence="low",
            primary_source_page=None,
            primary_source_filename=None,
        )

    concept = extract_query_concept(query)
    best_chunk = retrieved_chunks[0]
    top_text = clean_raw_text(best_chunk.get("text", ""))

    # 1. Try finding explicit definition across top 3 chunks
    for cand in retrieved_chunks[:3]:
        cand_text = clean_raw_text(cand.get("text", ""))
        definition = find_definition_sentence(concept, cand_text)
        if definition:
            # Clean up matched definition
            definition = definition.strip()
            if not definition.endswith((".", "!", "?")):
                definition += "."

            # Extract supporting key points
            points: list[str] = []
            sentences = split_sentences(cand_text)
            for s in sentences:
                s_lower = s.lower()
                # Find complementary sentences that explain objectives, roles, or mechanisms
                if definition.lower() not in s_lower and s_lower not in definition.lower() and any(k in s_lower for k in ["objective", "goal", "interface", "resource", "controls", "manages", "provides", "component"]):
                    if len(s) < 220 and s not in points:
                        points.append(s)
                if len(points) >= 3:
                    break

            return GeneratedAnswer(
                direct_answer=definition,
                key_points=points,
                confidence="high",
                primary_source_page=cand.get("page_number"),
                primary_source_filename=cand.get("filename"),
            )

    # 2. Heuristic extraction based on concept keyword matches
    ranked_sentences: list[tuple[float, str, dict]] = []
    concept_words = set(concept.lower().split())

    for cand in retrieved_chunks[:3]:
        cand_text = clean_raw_text(cand.get("text", ""))
        for s in split_sentences(cand_text):
            s_lower = s.lower()
            words_in_s = set(re.findall(r"\b[a-z0-9]+\b", s_lower))
            overlap = len(concept_words & words_in_s)
            score = float(overlap)
            # Bonus for definitional verbs
            if any(v in s_lower for v in [" is ", " are ", " defined as ", " refers to ", " acts as ", " provides "]):
                score += 1.5
            if 30 <= len(s) <= 300:
                ranked_sentences.append((score, s, cand))

    ranked_sentences.sort(key=lambda x: x[0], reverse=True)

    if ranked_sentences and ranked_sentences[0][0] >= 1.0:
        lead_sentence = ranked_sentences[0][1]
        lead_cand = ranked_sentences[0][2]
        supporting_points = [
            s for score, s, c in ranked_sentences[1:4]
            if s != lead_sentence and len(s) <= 220
        ]
        return GeneratedAnswer(
            direct_answer=lead_sentence,
            key_points=supporting_points,
            confidence="medium",
            primary_source_page=lead_cand.get("page_number"),
            primary_source_filename=lead_cand.get("filename"),
        )

    # 3. Fallback: extract the most coherent 1-2 leading sentences from top chunk
    top_sentences = split_sentences(top_text)
    fallback_answer = top_sentences[0] if top_sentences else top_text[:200] + "..."

    return GeneratedAnswer(
        direct_answer=fallback_answer,
        key_points=top_sentences[1:3] if len(top_sentences) > 1 else [],
        confidence="low",
        primary_source_page=best_chunk.get("page_number"),
        primary_source_filename=best_chunk.get("filename"),
    )
