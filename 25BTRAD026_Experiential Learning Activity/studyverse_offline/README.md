# StudyVerse Offline — Phase A

> **Local-first academic PDF search.**  
> Upload your study PDFs, search them with exact keywords and semantic meaning,  
> and read the original extracted source text — all locally, with no internet connection.

---

## Project Purpose

StudyVerse Offline lets students:
- Upload multiple academic PDFs and extract their text content.
- Search using exact terms (`nPr`, `F = ma`, `Newton`) **or** natural language (`What is permutation?`).
- See source-grounded results: the original PDF text, the page it came from, and a relevance score.
- No AI-generated answers. No cloud. No account required.

---

## Installation

```powershell
# 1. Navigate to the studyverse_offline directory
cd "C:\Users\dj845\Desktop\python experiantial learning\studyverse_offline"

# 2. Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt
```

---

## Run

```powershell
# From inside studyverse_offline/ with .venv active:
streamlit run app.py
```

Open your browser to `http://localhost:8501`.

---

## Folder Structure

```
studyverse_offline/
├── app.py              — Streamlit UI (Library / Search / About)
├── database.py         — SQLite layer (plain sqlite3, no ORM)
├── pdf_processor.py    — PyMuPDF extraction pipeline
├── search_engine.py    — Chunking + FTS5 + FAISS + hybrid ranking
├── requirements.txt    — Python dependencies
├── README.md           — This file
├── TEST_REPORT.md      — Manual test results
├── data/
│   ├── uploads/        — Saved PDF files (UUID-prefixed)
│   ├── indexes/        — FAISS index + metadata JSON per document
│   └── studyverse.db   — SQLite database (auto-created on first run)
└── tests/
    ├── test_pdf_processor.py
    └── test_search_engine.py
```

---

## Architecture

```
[Streamlit UI]
      │
      ├── pdf_processor.py
      │     PyMuPDF (fitz)
      │     page.get_text("text")  →  page-wise text
      │     Stored in SQLite: documents, page_text tables
      │
      ├── search_engine.py — Chunking
      │     700-char window / 120-char overlap / 150-char minimum
      │     Sentence-aware boundary detection
      │     Stored in SQLite: chunks table
      │
      ├── search_engine.py — Keyword Index (FTS5)
      │     SQLite FTS5 virtual table (chunk_fts)
      │     BM25 ranking
      │     Fallback: case-insensitive term frequency if FTS5 unavailable
      │
      ├── search_engine.py — Semantic Index (FAISS)
      │     SentenceTransformer: all-MiniLM-L6-v2
      │     Embeddings: float32, L2-normalised
      │     FAISS IndexFlatIP (inner product = cosine similarity after normalisation)
      │     Persisted: data/indexes/document_{id}.faiss + .json
      │
      └── search_engine.py — Hybrid Ranking
            final_score = 0.70 × semantic + 0.30 × keyword
            Per-request min-max normalisation
            Top-K selector, minimum relevance filter
```

---

## How Hybrid Search Works

1. **Semantic search:** The query is encoded by `all-MiniLM-L6-v2` into a 384-dimensional vector. The vector is L2-normalised. FAISS searches all indexed chunk embeddings using inner product (equivalent to cosine similarity after normalisation). Returns the top candidates per document.

2. **Keyword search:** The query is passed to SQLite FTS5, which uses BM25 to rank chunks by exact term frequency and inverse document frequency. Special characters (formulas, brackets) are safely escaped.

3. **Hybrid merge:** Both result sets are merged by chunk ID. Scores are independently min-max normalised to [0, 1] per request. The final score is:
   ```
   final_score = 0.70 × normalised_semantic + 0.30 × normalised_keyword
   ```
   Chunks that appear in only one result set receive 0 for the missing score.

4. **Score labels:** Scores are called "Semantic similarity", "Keyword relevance", and "Combined relevance". They are **not** called "accuracy".

---

## How to Use

### Library tab
1. Click **Upload PDFs** and drop your `.pdf` files.
2. Click **📤 Upload & Extract** — the app saves files and extracts text.
3. Click **⚡ Index** on any extracted document (or **⚡ Index All Eligible**).
4. The document will show "✅ Indexed" and is ready to search.

### Search Notes tab
1. Type a topic, question, or formula in the search box.
2. Choose a search mode (Hybrid is recommended).
3. Set **Top-K** (number of results) and **Minimum relevance** (keep at 0 initially).
4. Select which documents to search (all are pre-selected).
5. Click **🔍 Search**.
6. Each result card shows: filename, page, relevance scores, and the original extracted text.
7. Click **📖 Read Source Page** to see the full page text.

---

## Known Limitations

| Limitation | Details |
|---|---|
| **Text-based PDFs only** | Scanned or image PDFs cannot be indexed. No OCR is included. |
| **No LLM** | Results are retrieved verbatim from your PDFs. Nothing is generated or paraphrased. |
| **Relevance ≠ accuracy** | A high score means the chunk is relevant to your query, not that it is factually correct. |
| **FAISS index in files** | FAISS indexes are saved to `data/indexes/`. If you move the app, move the `data/` folder too. |
| **Single-user local** | The app is designed for a single student on one machine. No multi-user support. |
| **Formula matching** | Keyword search handles formula-like terms (`F = ma`) via phrase quoting. Very short single-character queries may return no results. |

---

## How to Run Tests

```powershell
cd "C:\Users\dj845\Desktop\python experiantial learning\studyverse_offline"
.\.venv\Scripts\Activate.ps1
python -m pytest tests/ -v
```

---

## Phase B Plans

Phase B will add (but is NOT included in this version):

- **Flashcard generation:** Auto-create Q&A cards from indexed chunks using rule-based extraction (no LLM).
- **Spaced repetition:** SM-2 algorithm to schedule card reviews.
- **Formula detection:** Highlight and index mathematical notation separately.
- **Multi-file search with document weighting:** Prefer specific documents per query.
- **Export:** Export search results to PDF or plain text.
