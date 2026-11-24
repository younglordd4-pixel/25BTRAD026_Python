# StudyVerse Offline — Phase A Test Report

> **Status:** Template — fill in actual results after running the app with real PDFs.  
> Run the 10 test queries listed below and record outcomes.

---

## Test Setup

| Item | Value |
|---|---|
| App version | Phase A |
| Run command | `streamlit run app.py` (from `studyverse_offline/`) |
| Search mode | Hybrid (default) unless otherwise noted |
| Test date | _Fill in_ |

---

## Documents Used

| # | Filename | Pages | Chunks | Notes |
|---|---|---|---|---|
| 1 | _e.g. permutations_combinations.pdf_ | _fill_ | _fill_ | Text-based academic PDF |
| 2 | _e.g. physics_newton.pdf_ | _fill_ | _fill_ | Text-based academic PDF |
| 3 | _e.g. biology_photosynthesis.pdf_ | _fill_ | _fill_ | Text-based academic PDF |
| 4 | _e.g. scanned_image.pdf (if available)_ | _fill_ | 0 | Scanned / image-only |

---

## Test Results

### Query 1 — `permutation`

| Field | Value |
|---|---|
| Query | `permutation` |
| Expected topic | Permutations / arrangements |
| Search mode | Keyword |
| Top-K | 3 |
| Min relevance | 0.0 |
| Top result filename | _fill_ |
| Top result page | _fill_ |
| Top result snippet | _fill first 100 chars_ |
| Relevant? | Yes / No |
| Combined relevance | _fill %_ |
| Semantic similarity | _fill %_ |
| Keyword relevance | _fill %_ |
| Notes | |

---

### Query 2 — `nPr`

| Field | Value |
|---|---|
| Query | `nPr` |
| Expected topic | Permutation formula notation |
| Search mode | Keyword |
| Top-K | 3 |
| Min relevance | 0.0 |
| Top result filename | _fill_ |
| Top result page | _fill_ |
| Top result snippet | _fill_ |
| Relevant? | Yes / No |
| Combined relevance | _fill %_ |
| Notes | FTS5 phrase-quoting used for formula |

---

### Query 3 — `What is permutation?`

| Field | Value |
|---|---|
| Query | `What is permutation?` |
| Expected topic | Permutations / arrangements |
| Search mode | Hybrid |
| Top-K | 3 |
| Min relevance | 0.0 |
| Top result filename | _fill_ |
| Top result page | _fill_ |
| Top result snippet | _fill_ |
| Relevant? | Yes / No |
| Combined relevance | _fill %_ |
| Semantic similarity | _fill %_ |
| Keyword relevance | _fill %_ |
| Notes | Semantic should dominate |

---

### Query 4 — `arrangement where order matters`

| Field | Value |
|---|---|
| Query | `arrangement where order matters` |
| Expected topic | Permutations |
| Search mode | Semantic |
| Top-K | 3 |
| Min relevance | 0.0 |
| Top result filename | _fill_ |
| Top result page | _fill_ |
| Top result snippet | _fill_ |
| Relevant? | Yes / No |
| Combined relevance | _fill %_ |
| Notes | Pure semantic — no exact terms |

---

### Query 5 — `Newton's second law`

| Field | Value |
|---|---|
| Query | `Newton's second law` |
| Expected topic | F = ma / Newton |
| Search mode | Hybrid |
| Top-K | 3 |
| Min relevance | 0.0 |
| Top result filename | _fill_ |
| Top result page | _fill_ |
| Top result snippet | _fill_ |
| Relevant? | Yes / No |
| Combined relevance | _fill %_ |
| Notes | |

---

### Query 6 — `F = ma`

| Field | Value |
|---|---|
| Query | `F = ma` |
| Expected topic | Newton's second law |
| Search mode | Keyword |
| Top-K | 3 |
| Min relevance | 0.0 |
| Top result filename | _fill_ |
| Top result page | _fill_ |
| Top result snippet | _fill_ |
| Relevant? | Yes / No |
| Combined relevance | _fill %_ |
| Notes | Formula — FTS5 phrase-quoting active |

---

### Query 7 — `What is photosynthesis?`

| Field | Value |
|---|---|
| Query | `What is photosynthesis?` |
| Expected topic | Photosynthesis / biology |
| Search mode | Hybrid |
| Top-K | 3 |
| Min relevance | 0.0 |
| Top result filename | _fill_ |
| Top result page | _fill_ |
| Top result snippet | _fill_ |
| Relevant? | Yes / No |
| Combined relevance | _fill %_ |
| Notes | Requires biology document to be indexed |

---

### Query 8 — `What is cricket?` (unrelated query)

| Field | Value |
|---|---|
| Query | `What is cricket?` |
| Expected topic | N/A — unrelated to study documents |
| Search mode | Hybrid |
| Top-K | 3 |
| Min relevance | 0.0 |
| Top result filename | _fill_ |
| Top result page | _fill_ |
| Top result snippet | _fill_ |
| Relevant? | No (expected) |
| Combined relevance | _fill % — expected to be low_ |
| Notes | Low scores confirm the system does not hallucinate. |

---

### Query 9 — High Threshold Test

| Field | Value |
|---|---|
| Query | `permutation` |
| Expected topic | Permutations |
| Search mode | Hybrid |
| Top-K | 3 |
| Min relevance | **0.90** |
| Top result | Expected: filtered out or very high score only |
| Message shown | "Matches were found, but none met the selected minimum relevance." (if filtered) |
| Notes | Confirms minimum relevance slider works correctly |

---

### Query 10 — Scanned PDF Warning Test

| Field | Value |
|---|---|
| Query | N/A (upload only) |
| Action | Upload a scanned / image-only PDF |
| Expected message | "No searchable text was found. This PDF may be scanned or image-based. OCR is not included in this version." |
| Message shown? | Yes / No / File not available |
| Chunks created | 0 (expected) |
| Notes | If no scanned PDF is available, skip this test and mark N/A |

---

## Limitations Observed

| Limitation | Observed? | Notes |
|---|---|---|
| Scanned PDFs cannot be indexed | _Yes/No_ | |
| Very short formulas (single char) return no keyword results | _Yes/No_ | |
| FTS5 not available in some SQLite builds (fallback used) | _Yes/No_ | Check About/Debug tab |
| FAISS index requires re-indexing if moved to new machine | _Yes/No_ | |
| Relevance scores vary by document set | _Yes/No_ | Min-max normalised per request |
| No LLM — cannot answer questions, only retrieves text | By design | |

---

## Summary

| Query | Relevant? | Mode | Top Score |
|---|---|---|---|
| permutation | | Keyword | |
| nPr | | Keyword | |
| What is permutation? | | Hybrid | |
| arrangement where order matters | | Semantic | |
| Newton's second law | | Hybrid | |
| F = ma | | Keyword | |
| What is photosynthesis? | | Hybrid | |
| What is cricket? (unrelated) | No (expected) | Hybrid | |
| High threshold (0.90) | Filtered (expected) | Hybrid | |
| Scanned PDF warning | N/A | Upload | |
