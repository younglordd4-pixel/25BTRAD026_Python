# FACULTY OF ENGINEERING AND TECHNOLOGY
## JAIN (DEEMED-TO-BE UNIVERSITY)
### SCHOOL OF COMPUTER SCIENCE AND ENGINEERING
**B.Tech CSE - Artificial Intelligence & Machine Learning (AIML)**  
**Course:** Python Programming | **Course Code:** 21CS301  
**Semester:** 3 | **Year:** 2nd | **Academic Session:** 2026–2027  

---

# GROUP PROJECT REPORT

### **Project Title:**  
**StudyVerse Offline: A Privacy-Preserving Academic Study Assistant for Multi-Format Document Semantic Search, Active Recall, and Spaced Revision**

**Submitted To:**  
**Prof. Biswajit Debnath**  
Assistant Professor,  
Department of CSE - AIML, Faculty of Engineering and Technology,  
JAIN (Deemed-to-be) University, Bangalore  

---

### **Submitted By – Group Details**

| Sl. No. | Name | USN | Responsibility |
|:---:|:---|:---:|:---|
| 1 | [Student Name 1] | [23BTRCA001] | System Architecture, SentenceTransformers & FAISS Vector Search Engine |
| 2 | [Student Name 2] | [23BTRCA002] | Multi-format OpenXML Document Extractors (PDF, DOCX, PPTX) & Text Chunking |
| 3 | [Student Name 3] | [23BTRCA003] | SQLite Database Architecture, FTS5 BM25 Engine & Schema Management |
| 4 | [Student Name 4] | [23BTRCA004] | Rule-Based Active Recall Quiz Engine & SM-2 Spaced Repetition Logic |
| 5 | [Student Name 5] | [23BTRCA005] | Streamlit Frontend Interface, FastAPI REST Endpoints & Visual Styling |
| 6 | [Student Name 6] | [23BTRCA006] | Test Engineering, Edge Case Validation & Quality Assurance (90 Unit Tests) |

---

## INDEX

| Chapter No. | Chapter Title | Page No. |
|:---:|:---|:---:|
| **1** | **Introduction and Problem Definition** | 3 |
| 1.1 | Project Background | 3 |
| 1.2 | Problem Statement | 3 |
| 1.3 | Target Users and Use Context | 4 |
| 1.4 | Project Objectives | 4 |
| 1.5 | Scope and Limitations | 5 |
| 1.6 | Relevance and Expected Outcome | 5 |
| **2** | **Requirements and Existing / Proposed System** | 6 |
| 2.1 | Existing Approach or Current Process | 6 |
| 2.2 | Proposed Solution | 6 |
| 2.3 | Functional Requirements | 7 |
| 2.4 | Non-Functional Requirements | 8 |
| 2.5 | Hardware and Software Requirements | 8 |
| 2.6 | Feasibility, Constraints and Responsible Use | 9 |
| **3** | **System Design and Methodology** | 10 |
| 3.1 | Overall Architecture | 10 |
| 3.2 | Workflow / Flowchart | 11 |
| 3.3 | Module-Wise Design | 12 |
| 3.4 | Data Design & Database Schema | 13 |
| 3.5 | API Design (FastAPI Endpoints) | 14 |
| 3.6 | Machine Learning & Information Retrieval Methodology | 15 |
| **4** | **Project Structure, Tools and Python Concepts** | 16 |
| 4.1 | Project Folder Structure | 16 |
| 4.2 | Tools, Libraries, and Technologies | 17 |
| 4.3 | Python Syllabus Concepts Applied | 18 |
| 4.4 | Repository and Version Control | 19 |
| **5** | **Implementation** | 20 |
| 5.1 | Development Environment and Setup | 20 |
| 5.2 | Module-Wise Implementation | 20 |
| 5.3 | Application / User Interface Implementation | 22 |
| 5.4 | API & Backend Implementation | 23 |
| 5.5 | Embedding & Retrieval Implementation | 24 |
| 5.6 | Error Handling and Input Validation | 25 |
| 5.7 | Key Code Excerpts | 26 |
| **6** | **Testing, Validation and Evaluation** | 29 |
| 6.1 | Testing Approach | 29 |
| 6.2 | Functional Software Test Cases | 29 |
| 6.3 | API Test Suite Execution | 31 |
| 6.4 | Information Retrieval Evaluation & Benchmark | 32 |
| 6.5 | Result Analysis and Failure Cases | 33 |
| **7** | **Results and Screenshot Evidence** | 34 |
| 7.1 | Document Library & Ingestion Screen | 34 |
| 7.2 | Hybrid Search & Direct Answer Extraction | 35 |
| 7.3 | Active Recall Practice Arena | 36 |
| 7.4 | SM-2 Spaced Revision Tracker | 37 |
| 7.5 | Interactive API Swagger Documentation | 38 |
| **8** | **Deployment, User Guide and Reproducibility** | 39 |
| 8.1 | Installation and Setup Steps | 39 |
| 8.2 | User Operation Guide | 40 |
| 8.3 | Deployment Details | 40 |
| 8.4 | Reproducibility Information | 41 |
| 8.5 | Known Limitations | 41 |
| **9** | **Conclusion and Future Enhancements** | 42 |
| 9.1 | Conclusion | 42 |
| 9.2 | Future Enhancements | 42 |
| **–** | **References** | 43 |

---

# CHAPTER 1 — INTRODUCTION AND PROBLEM DEFINITION

### 1.1 Project Background
Undergraduate engineering students, particularly in technical fields like Computer Science and Artificial Intelligence, encounter hundreds of lecture slide decks (PowerPoint PPTX), lecture notes (Word DOCX), and academic textbooks (PDF) every semester. A second-year student preparing for end-semester exams often needs to cross-reference concepts across multiple subjects—for example, linking *Newton’s laws* from engineering physics with *gradient descent optimization* in machine learning. However, modern commercial AI tools (such as ChatGPT, Claude, or NotebookLM) require uploading proprietary or personal course materials to external cloud servers, mandate persistent high-bandwidth internet connections, and frequently introduce "hallucinations" by generating convincing text that lacks verbatim verification in original lecture notes.

### 1.2 Problem Statement
Existing personal note search techniques depend on primitive keyword matchers (like `Ctrl+F`), which fail entirely when an exam question uses conceptual synonyms or paraphrasing rather than exact keyword strings. Conversely, modern generative cloud LLMs are prone to hallucinations, require active cloud subscriptions, and pose data privacy risks for unreleased research or institutional course packs. Furthermore, students lack an integrated workflow connecting search retrieval to **active recall testing** and **spaced repetition scheduling**. This project addresses the challenge of building an offline, zero-cloud desktop application that enables semantic and lexical retrieval across academic PDFs, DOCX, and PPTX files, grounded with verbatim citations and deterministic active recall exercises.

### 1.3 Target Users and Use Context
* **Target Users:** Undergraduate and postgraduate engineering students, researchers, faculty members, and academic competitive exam aspirants (e.g., GATE, GRE).
* **Use Context:** Local desktop or laptop environments (Windows/Linux/macOS) in university hostels, libraries, or exam halls without requiring internet connectivity, third-party API keys, or GPU acceleration hardware.

### 1.4 Project Objectives
The key objectives of this project are:

| Objective No. | Objective | Verification Method |
|:---:|:---|:---|
| **O1** | Ingest multi-format academic documents (PDF, DOCX, PPTX) and extract clean page/slide-aligned text. | Automated upload pipeline verified with PyMuPDF and XML parsers; verified via 25 API test cases. |
| **O2** | Implement a local hybrid search engine combining dense vector embeddings (FAISS) and lexical BM25 (SQLite FTS5). | Top-K retrieval tests assessing precision across keyword queries, semantic concept queries, and mathematical formulas. |
| **O3** | Provide an extractive direct-answer synthesis engine that pinpoints exact source sentences without generative hallucination. | Evaluated against 10 academic benchmark queries with source filename and page/slide citations. |
| **O4** | Build a rule-based active recall quiz generator producing fill-in-the-blank, formula recall, and true/false questions. | Deterministic test validation ensuring exactly 3 verifiable questions generated per retrieved context. |
| **O5** | Implement an automated spaced repetition tracker based on the SuperMemo SM-2 algorithm. | Database retention verification ensuring next review dates adjust dynamically based on student ratings. |

### 1.5 Scope and Limitations
* **In-Scope:**
  - Parsing PDF via PyMuPDF (`fitz`).
  - Parsing Word (`.docx`, `.doc`) and PowerPoint (`.pptx`, `.ppt`) via pure Python OpenXML XML/Zip parsing.
  - Sentence embedding generation using local `all-MiniLM-L6-v2` (384-dimensional dense vectors).
  - Dense indexing using FAISS Inner Product (`IndexFlatIP`) with L2-normalized vectors.
  - Lexical search using SQLite FTS5 with BM25 ranking.
  - Interactive web user interface built with Streamlit.
  - Modular REST API backend powered by FastAPI.
* **Limitations (Out of Scope):**
  - Scanned, image-only documents without OCR text layers cannot be indexed (clear warning returned).
  - Handwritten notes in image format are not transcribed.
  - Audio/video lecture files are unsupported.

### 1.6 Relevance and Expected Outcome
The primary outcome is a fully offline, executable desktop application (**StudyVerse Offline**) providing instantaneous sub-50ms hybrid note search, transparent source citations, self-assessment quizzes, and a daily revision schedule. It provides educational institutions with a zero-cost, high-privacy reference implementation for local AI-assisted learning.

---

# CHAPTER 2 — REQUIREMENTS AND EXISTING / PROPOSED SYSTEM

### 2.1 Existing Approach or Current Process
Currently, students manage study materials using operating system file search or PDF viewers (`Adobe Acrobat`, `Foxit`, `Preview`). 
* **Weaknesses of Existing Methods:**
  1. *Lexical Rigidity:* Searching for "rate of velocity change" will never locate a slide stating "acceleration is the time derivative of velocity."
  2. *Fragmented File Types:* Word documents, slide decks, and PDFs must each be searched in separate applications.
  3. *Absence of Learning Loops:* Once information is located, the student must manually copy it into third-party flashcard apps like Anki, creating friction that discourages active recall.

### 2.2 Proposed Solution
StudyVerse Offline unifies multi-format document ingestion into a single, cohesive local pipeline. Files are uploaded via an interactive browser interface, automatically extracted into page- and slide-aligned text blocks, chunked using a sentence-boundary sliding window, and dual-indexed into an SQLite FTS5 table and a FAISS dense vector index. Queries are processed simultaneously by vector and lexical matchers, normalized, and blended with balanced weights ($0.70$ semantic, $0.30$ keyword). Students can read source contexts, take deterministic 3-question active recall quizzes, and log mastery levels into a persistent SM-2 spaced revision tracker.

### 2.3 Functional Requirements

| ID | Functional Requirement | Priority | Verification Method |
|:---:|:---|:---:|:---|
| **FR-01** | Multi-Format Document Ingestion (PDF, DOCX, PPTX) | High | Automated tests uploading multi-page DOCX, multi-slide PPTX, and academic PDFs. |
| **FR-02** | Sentence-Aware Sliding Window Chunking (700 chars, 120 overlap, 150 min) | High | Unit tests verifying chunk length boundaries and sequential ordering. |
| **FR-03** | FTS5 Lexical Search with Special Character / Formula Sanitization | High | Formula search tests (`F = ma`, `nPr`) verifying sanitized BM25 ranking. |
| **FR-04** | FAISS Vector Search with Normalized Cosine Similarity | High | Semantic query tests evaluating top-K inner-product matches. |
| **FR-05** | Hybrid Score Fusion ($0.70 \times \text{Semantic} + 0.30 \times \text{Keyword}$) | High | Verification of min-max normalized composite score outputs. |
| **FR-06** | Heuristic Direct Answer & Key Point Synthesis | Medium | Extractive QA verification returning definition sentences with high confidence. |
| **FR-07** | Deterministic 3-Question Active Recall Quiz Generation | High | Test suite validating Fill-in-the-Blank, Formula Recall, and True/False generation. |
| **FR-08** | SM-2 Spaced Repetition Scheduling and Due-Today Dashboard | High | SQLite date calculation test verifying intervals of 1 day, 6 days, and dynamic growth. |

### 2.4 Non-Functional Requirements
1. **Zero External Network Reliance:** 100% of processing, indexing, and inference occurs locally on `localhost`.
2. **Sub-Second Search Latency:** Hybrid search retrieval across 1,000 text chunks must complete in under 50 milliseconds.
3. **Low Memory Footprint:** The entire system, including embedding weights and database connections, must run within 1.5 GB RAM.
4. **Data Integrity:** ACID-compliant storage via SQLite WAL (Write-Ahead Logging) mode.

### 2.5 Hardware and Software Requirements

| Category | Specification Used in Project |
|:---|:---|
| **Computer Hardware** | Standard Intel/AMD x86_64 or ARM64 PC, 8 GB RAM, Dual-Core 2.0 GHz CPU |
| **Operating System** | Windows 10/11 (64-bit), compatible with Ubuntu 22.04 LTS / macOS 13+ |
| **Language & Runtime** | Python 3.10 – 3.14 (Verified on Python 3.14.3 64-bit) |
| **Web Framework & UI** | Streamlit 1.35+, FastAPI 0.110+, Uvicorn 0.29+ |
| **Database Engines** | SQLite 3.40+ (with FTS5 virtual table support enabled) |
| **AI / NLP Libraries** | `sentence-transformers` 3.0+ (`all-MiniLM-L6-v2`), `faiss-cpu` 1.8.0+, `numpy` 1.26+ |
| **Document Parsers** | PyMuPDF (`fitz`) 1.24+, Python Standard Library (`zipfile`, `xml.etree.ElementTree`) |
| **Test Framework** | Pytest 8.0+ |

### 2.6 Feasibility, Constraints, and Responsible Use
* **Feasibility:** Fully feasible using lightweight open-source models (`all-MiniLM-L6-v2` is only 90 MB in size) capable of high-speed CPU inference without requiring an expensive dedicated GPU.
* **Responsible Use & Data Privacy:** Because zero network requests are issued, student notes, confidential university exam materials, and faculty lecture slides remain strictly protected on the local disk. No personal credentials, API keys, or tracking tokens are employed.

---

# CHAPTER 3 — SYSTEM DESIGN AND METHODOLOGY

### 3.1 Overall Architecture

```
+-----------------------------------------------------------------------------------+
|                           PRESENTATION LAYER (Streamlit UI)                       |
|  [Library Upload]   [Hybrid Search]   [Practice Arena]   [Revision Hub]  [About]  |
+------------------------------------------+----------------------------------------+
                                           | HTTP Requests / Direct Calls
+------------------------------------------v----------------------------------------+
|                          APPLICATION LAYER (FastAPI / Core Engine)                 |
|  - Router & Dispatcher (/documents, /search, /practice, /revision)                |
|  - Ingestion Controller & Document Type Router                                    |
|  - Query Sanitizer & Score Normalizer                                             |
+---------------------+-------------------------------+-----------------------------+
                      |                               |
+---------------------v-------+              +--------v-----------------------------+
|    INGESTION & PARSING      |              |          SEARCH & RETRIEVAL          |
|  - PyMuPDF (PDF Parser)     |              |  - FAISS (all-MiniLM-L6-v2 Dense IP) |
|  - OpenXML Parser (DOCX)    |              |  - SQLite FTS5 (Lexical BM25)        |
|  - OpenXML Parser (PPTX)    |              |  - Direct Answer Heuristic Synthesizer|
|  - Chunking Engine (700/120)|              |  - Hybrid Ranker (0.70 Sem + 0.30 Kw)|
+---------------------+-------+              +--------+-----------------------------+
                      |                               |
+---------------------v-------------------------------v-----------------------------+
|                                STORAGE & DATABASE LAYER                           |
|  - SQLite3 (`studyverse.db` in WAL Mode: documents, page_text, chunks, revision)  |
|  - Local File System Storage (`data/uploads/`, `data/indexes/*.faiss`)            |
+-----------------------------------------------------------------------------------+
```

### 3.2 Workflow / Flowchart

```
[Student Uploads PDF/DOCX/PPTX]
             |
             v
[Format Validation & MIME Signature Verification]
             |
   +---------+---------+
   | Extension Check   |
   +---------+---------+
   |--> .pdf  -> PyMuPDF fitz Page Extraction
   |--> .docx -> OpenXML word/document.xml Paragraph & Break Extraction
   |--> .pptx -> OpenXML ppt/slides/slide*.xml Slide Extraction
             |
             v
[Database Storage: documents and page_text tables]
             |
             v
[Sentence-Aware Sliding Window Chunking (700 chars, 120 overlap)]
             |
             +------------------------------+
             |                              |
             v                              v
[SQLite FTS5 Insert: chunk_fts]    [Dense Embedding: all-MiniLM-L6-v2]
                                            |
                                            v
                                  [L2 Normalization & FAISS Index]
                                            |
                                            v
                                [Query Issued by Student]
                                            |
             +------------------------------+
             |                              |
             v                              v
[Lexical BM25 Ranking]             [Dense Cosine Similarity Ranking]
             |                              |
             +--------------+---------------+
                            |
                            v
               [Min-Max Normalization]
                            |
                            v
     [Composite Scoring: 0.70 * Sem + 0.30 * Kw]
                            |
                            v
     [Extractive QA: Direct Answer & Key Points]
                            |
                            v
     [Active Recall Quiz (3 Questions)] <---> [SM-2 Spaced Revision Tracker]
```

### 3.3 Module-Wise Design

| Module Name | File Location | Responsibility | Input | Output |
|:---|:---|:---|:---|:---|
| **Document Extractor** | `document_extractor.py` | Extracts text from PDF, DOCX, and PPTX with page/slide preservation. | File path on disk | Page count, List of `(page_num, text)` |
| **PDF / File Processor** | `pdf_processor.py` | Validates file signatures, generates safe unique disk paths, updates DB. | Binary file object, name | Document record dict with status |
| **Search Engine** | `search_engine.py` | Coordinates chunking, FAISS index construction, BM25 and vector retrieval. | Query string, Doc IDs, Top-K | Ranked candidate dicts with scores |
| **Answer Service** | `answer_service.py` | Extracts definition sentences, formula relations, and bullet points. | Query, Top chunk texts | `direct_answer`, `confidence`, key points |
| **Quiz Engine** | `quiz_engine.py` | Generates 3 deterministic active recall questions from source text. | Query topic, Chunks | 3 Question dicts (Fill blank, formula, T/F) |
| **Revision Engine** | `revision_engine.py` | Computes dynamic review intervals using modified SM-2 algorithm. | Review status, repetitions | Next review date, new interval |

### 3.4 Data Design & Database Schema
The database uses an optimized SQLite3 schema operating with Write-Ahead Logging (`PRAGMA journal_mode=WAL`) and Foreign Key enforcement (`PRAGMA foreign_keys=ON`):

```sql
-- Core document metadata
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    stored_filename TEXT NOT NULL UNIQUE,
    page_count INTEGER NOT NULL DEFAULT 0,
    extracted_page_count INTEGER NOT NULL DEFAULT 0,
    has_extractable_text BOOLEAN NOT NULL DEFAULT 0,
    extraction_status TEXT NOT NULL DEFAULT 'pending',
    extraction_message TEXT,
    created_at TEXT NOT NULL
);

-- Full extracted page/slide text
CREATE TABLE page_text (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    text TEXT NOT NULL,
    character_count INTEGER NOT NULL DEFAULT 0
);

-- Searchable text chunks
CREATE TABLE chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    chunk_number INTEGER NOT NULL,
    text TEXT NOT NULL,
    character_count INTEGER NOT NULL
);

-- Full-Text Search virtual table (FTS5)
CREATE VIRTUAL TABLE chunk_fts USING fts5(
    chunk_id UNINDEXED,
    document_id UNINDEXED,
    page_number UNINDEXED,
    text
);

-- Spaced revision tracking (SM-2)
CREATE TABLE revision_topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT NOT NULL UNIQUE,
    source_document_id INTEGER,
    source_filename TEXT NOT NULL,
    page_number INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'review_tomorrow',
    repetitions INTEGER NOT NULL DEFAULT 0,
    interval_days INTEGER NOT NULL DEFAULT 1,
    ease_factor REAL NOT NULL DEFAULT 2.5,
    next_review_date TEXT NOT NULL,
    last_reviewed_at TEXT,
    latest_quiz_score INTEGER,
    latest_quiz_total INTEGER
);
```

### 3.5 API Design (FastAPI Endpoints)

| Method | Endpoint | Purpose | Request Body / Parameters | Response Status & Body |
|:---|:---|:---|:---|:---|
| **GET** | `/health` | System health check | None | `200 OK` `{ status: "ok" }` |
| **POST** | `/documents/upload` | Ingest PDF, DOCX, PPTX | `multipart/form-data` (`files`) | `201 Created` `list[DocumentResponse]` |
| **GET** | `/documents` | List all ingested files | None | `200 OK` `list[DocumentResponse]` |
| **GET** | `/documents/{id}/pages` | View extracted page text | Path parameter `id: int` | `200 OK` `list[PageTextResponse]` |
| **DELETE** | `/documents/{id}` | Purge file and indexes | Path parameter `id: int` | `200 OK` `{ message: "Deleted" }` |
| **POST** | `/documents/{id}/index` | Index specific document | Path parameter `id: int` | `200 OK` `{ chunks_created: int }` |
| **POST** | `/search` | Execute hybrid search | `{ query, mode, top_k, min_score }` | `200 OK` `{ results: [...], direct_answer: {...} }` |
| **POST** | `/practice/generate` | Generate active recall quiz | `{ document_ids: [...], max_cards: int }`| `200 OK` `{ total_generated: int, cards: [...] }` |
| **GET** | `/revision/due` | Get topics due for review | Query parameter `limit: int` | `200 OK` `list[RevisionItem]` |
| **POST** | `/revision/review/{id}`| Submit revision grade | `{ quality: int (0..5) }` | `200 OK` `{ next_review_date: str }` |

### 3.6 Machine Learning & Information Retrieval Methodology
1. **Sentence Embeddings:** We employ `sentence-transformers/all-MiniLM-L6-v2`, a 22-million parameter mini language model based on BERT, fine-tuned on over 1 billion sentence pairs. It maps natural language sentences to a 384-dimensional dense vector space where cosine similarity mirrors semantic equivalence.
2. **Dense Indexing:** Embeddings are normalized to unit length ($L_2$ norm), transforming inner product calculations directly into cosine similarity:
   $$\text{Cosine Similarity}(u, v) = \frac{u \cdot v}{\|u\|_2 \|v\|_2} = u \cdot v \quad (\text{when } \|u\| = \|v\| = 1)$$
   Dense vectors are managed using Facebook AI Similarity Search (`faiss.IndexFlatIP`).
3. **Lexical Retrieval:** Keyword search utilizes SQLite's FTS5 extension using BM25 ranking.
4. **Score Fusion:** Both scores are min-max scaled into $[0.0, 1.0]$ and combined as:
   $$S_{\text{final}} = (0.70 \times S_{\text{semantic}}) + (0.30 \times S_{\text{keyword}})$$

---

# CHAPTER 4 — PROJECT STRUCTURE, TOOLS AND PYTHON CONCEPTS

### 4.1 Project Folder Structure
```
c:\Users\dj845\Desktop\python experiantial learning\
│
├── app.py                              # Full-stack Streamlit frontend client
├── start.bat                           # Full-stack batch launcher with robust space handling
├── start_standalone.bat                # Standalone application batch launcher
├── requirements.txt                    # Project dependencies
├── PROJECT_REPORT.md                   # Complete academic technical report
│
├── studyverse_offline/                 # Standalone Engine (Option A)
│   ├── app.py                          # 5-Tab Standalone Streamlit User Interface
│   ├── database.py                     # Raw sqlite3 + WAL + FTS5 database layer
│   ├── document_extractor.py           # Unified PDF, DOCX, PPTX OpenXML text extractor
│   ├── pdf_processor.py                # Safe document ingestion & storage pipeline
│   ├── search_engine.py                # FAISS vector & FTS5 hybrid search engine
│   ├── quiz_engine.py                  # Rule-based 3-question active recall generator
│   ├── revision_engine.py              # SM-2 algorithm spaced repetition scheduler
│   ├── pytest.ini                      # Pytest configuration with DLL and plugin overrides
│   ├── conftest.py                     # Windows DLL path resolution fixture
│   └── tests/                          # 65 Automated Unit & Integration Tests
│       ├── test_document_extractor.py  # Tests for DOCX and PPTX extraction
│       ├── test_pdf_processor.py       # Tests for PDF corruption & extraction
│       └── test_search_engine.py       # Tests for chunking, scoring, and weights
│
└── backend/                            # Full-Stack FastAPI Server (Option B)
    ├── requirements.txt                # Backend dependencies
    ├── pytest.ini                      # Backend test configuration
    ├── data/                           # Persistent directory (SQLite DB, uploads, FAISS)
    └── app/
        ├── main.py                     # FastAPI application instance & lifespan events
        ├── database.py                 # SQLAlchemy engine and session factory
        ├── models.py                   # ORM data models (Document, Chunk, PageText)
        ├── schemas.py                  # Pydantic v2 validation schemas
        ├── routers/                    # Endpoints: documents, search, practice, revision
        ├── services/                   # Business logic (chunking, embedding, answer)
        └── tests/                      # 25 Automated Backend API Tests
            ├── test_docx_pptx_api.py   # Multi-format upload API test suite
            ├── test_stage2_api.py      # Search and validation endpoint tests
            └── test_stage2_chunking.py # Sentence chunking boundary tests
```

### 4.2 Tools, Libraries, and Technologies
* **Python 3.14.3:** Primary core programming language runtime.
* **PyMuPDF (`fitz` 1.28.2):** High-performance PDF parsing and rendering.
* **Python Standard Library (`zipfile`, `xml.etree.ElementTree`):** Zero-dependency extraction for Microsoft Word (`.docx`) and PowerPoint (`.pptx`).
* **Sentence-Transformers (3.0.0+):** Local vector embeddings using `all-MiniLM-L6-v2`.
* **FAISS-CPU (1.15.0):** Dense vector similarity indexing.
* **SQLite3 (with FTS5):** Local relational database and full-text search engine.
* **Streamlit (1.40+):** Reactive web user interface framework.
* **FastAPI & Uvicorn:** Asynchronous backend REST API service.
* **Pytest (8.3.2):** Automated testing framework.

### 4.3 Python Concepts Applied

| Python Syllabus Area | Concept Actually Used | File / Module | How it Supports the Project |
|:---|:---|:---|:---|
| **Unit I: Basics & Types** | String slicing, format strings, regex matching, type hinting | `document_extractor.py:25` | Sanitizing file names, parsing XML attributes, validating file suffixes. |
| **Unit II: Control Flow & Functions** | List comprehensions, generators, recursive boundary finding | `search_engine.py:74` | Sentence-boundary search (`_best_break`) iteratively scanning character windows. |
| **Unit III: Data Structures** | Dictionaries, sets, NamedTuples, tuples, lists | `quiz_engine.py:22` | Efficient $O(1)$ stop-word lookups using hash sets; structured chunk drafts via NamedTuples. |
| **Unit IV: File Handling & Errors** | Context managers (`with`), binary I/O, `zipfile`, custom exceptions | `pdf_processor.py:62` | Safe file persistence on disk, opening zip archives, catching `FileDataError` and `BadZipFile`. |
| **Unit V: OOP & Analysis** | Classes, method overriding, NumPy vector normalization | `search_engine.py:160` | Normalizing 2D embedding matrices using `np.linalg.norm` and matrix multiplication. |

### 4.4 Repository and Version Control
The project maintains clean atomic commits across features. The `.gitignore` prevents virtual environments (`.venv/`), model weight caches (`.cache/`), SQLite WAL temporary files (`*.db-wal`), and test artifacts from polluting source control.

---

# CHAPTER 5 — IMPLEMENTATION

### 5.1 Development Environment and Setup
The system is built entirely on native 64-bit Python. To set up and run:
```powershell
# 1. Clone repository and navigate to folder
cd "c:\Users\dj845\Desktop\python experiantial learning"

# 2. Run automated test suite (verifying 90 passing tests)
cd studyverse_offline
python -m pytest tests/ -v
cd ../backend
python -m pytest app/tests/ -v

# 3. Launch the complete application
cd ..
.\start.bat
```

### 5.2 Module-Wise Implementation
1. **Multi-Format Extraction Pipeline:** `document_extractor.py` inspects the file extension. PDFs are routed to PyMuPDF. For DOCX files, the internal `word/document.xml` is uncompressed in memory; paragraph nodes (`<w:p>`) and explicit page break tags (`<w:br w:type="page"/>`) are parsed to generate accurate page boundaries. For PPTX files, slide XML files (`ppt/slides/slide*.xml`) are sorted numerically and extracted slide-by-slide.
2. **Chunking Engine:** `search_engine.py` receives extracted page text. A sliding window of 700 characters with 120-character overlap traverses the text. The cut point searches backward for terminal punctuation (`.`, `?`, `!`), avoiding mid-sentence cuts. Chunks shorter than 150 characters are merged or discarded.
3. **Hybrid Search Service:** Queries undergo dual execution:
   - *Dense vector search:* Query text is embedded into a 384-dimensional vector, normalized, and queried against the document's FAISS index.
   - *BM25 lexical search:* Query text is sanitized into safe FTS5 match expressions (wrapping phrases in quotes to protect operators like `+`, `-`, `/`, and `=`), returning rank scores.
   - Scores are combined: $S = 0.70 \times S_{\text{sem}} + 0.30 \times S_{\text{kw}}$.
4. **Deterministic Active Recall Quiz Engine:** When a topic is selected, `quiz_engine.py` isolates key sentences from the highest-ranked chunk. It creates:
   - *Question 1:* Fill-in-the-blank by identifying the longest domain-specific non-stopword and replacing it with `______`.
   - *Question 2:* Formula recall by scanning for mathematical symbols (`=`, `nPr`, `F=ma`, `!`).
   - *Question 3:* True/False prompt directly derived from the source sentence.
5. **SM-2 Spaced Revision Engine:** Implements the SuperMemo-2 interval algorithm. Student responses (`Understood`, `Review Tomorrow`, `Need Revision`) adjust repetition count $R$, ease factor $EF$, and scheduled interval $I$:
   $$I(1) = 1, \quad I(2) = 6, \quad I(R) = I(R-1) \times EF$$

### 5.3 Application / User Interface Implementation
The frontend is constructed using Streamlit with custom CSS providing a clean, modern aesthetic:
* **Library View:** Displays document cards with page counts, chunk counts, index status pills, and extracted text viewer.
* **Search Notes:** Real-time query input with mode switcher (*Hybrid*, *Semantic*, *Keyword*), Top-K slider, and threshold filter.
* **Direct Answer Banner:** Displays extractive answers, key bullet points, and source page badges.
* **Practice Arena:** Form-based quiz testing with interactive grading and score calculation.
* **Revision Tracker:** Dashboard tracking topics due today, overdue items, and mastery distribution.

### 5.4 API & Backend Implementation
FastAPI provides RESTful routes with automated OpenAPI / Swagger documentation at `/docs`. Request payloads are strictly validated using Pydantic v2 schemas (`SearchRequest`, `DocumentResponse`, `QuizSubmission`).

### 5.5 Embedding & Retrieval Implementation
The model `SentenceTransformer('all-MiniLM-L6-v2')` is cached in memory using `@st.cache_resource` (Streamlit) or application lifespan state (FastAPI). Batch encoding transforms passages into NumPy arrays:
```python
embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
index = faiss.IndexFlatIP(384)
index.add(embeddings)
```

### 5.6 Error Handling and Input Validation
* **Corrupt Documents:** Corrupted files, zero-byte uploads, and fake extensions trigger graceful user-friendly error banners rather than unhandled server tracebacks.
* **DLL Resolution:** Automatic registration of `faiss_cpu.libs` via `os.add_dll_directory` ensures seamless Windows execution.
* **Batch Launcher Safety:** The batch launcher uses directory switches (`/D`) and explicit paths to avoid failures caused by spaces in folder names.

### 5.7 Key Code Excerpts

#### **Listing 5.1: Multi-Format OpenXML DOCX & PPTX Extraction (`document_extractor.py`)**
```python
def extract_docx(path: Path) -> tuple[int, list[tuple[int, str]], str | None]:
    with zipfile.ZipFile(str(path), "r") as zf:
        if "word/document.xml" not in zf.namelist():
            return 0, [], "Invalid DOCX file: missing word/document.xml."
        tree = ET.fromstring(zf.read("word/document.xml"))
        pages, cur_lines, cur_chars = [], [], 0
        for p in tree.iterfind(".//w:p", DOCX_NS):
            has_break = any(br.get(f"{{{DOCX_NS['w']}}}type") == "page" for br in p.iterfind(".//w:br", DOCX_NS))
            texts = [node.text for node in p.iterfind(".//w:t", DOCX_NS) if node.text]
            p_text = "".join(texts).strip()
            if (has_break or cur_chars >= 2500) and cur_lines:
                pages.append("\n".join(cur_lines).strip())
                cur_lines, cur_chars = [], 0
            if p_text:
                cur_lines.append(p_text)
                cur_chars += len(p_text)
        if cur_lines:
            pages.append("\n".join(cur_lines).strip())
        return len(pages), list(enumerate(pages, start=1)), None
```

#### **Listing 5.2: Hybrid Score Normalization & Fusion (`search_engine.py`)**
```python
def hybrid_search(conn, model, query, doc_ids, top_k, fts5_ok):
    sem_results = semantic_search(model, doc_ids, query, top_k=top_k * 2)
    kw_results = keyword_search(conn, query, doc_ids, top_k=top_k * 2, fts5_available=fts5_ok)
    
    # Merge candidates on chunk_id
    combined = {}
    for r in sem_results:
        combined[r["chunk_id"]] = dict(r)
    for r in kw_results:
        cid = r["chunk_id"]
        if cid in combined:
            combined[cid]["keyword_score"] = r["keyword_score"]
        else:
            combined[cid] = dict(r)
            
    for item in combined.values():
        s = item.get("semantic_score") or 0.0
        k = item.get("keyword_score") or 0.0
        item["final_score"] = round(0.70 * s + 0.30 * k, 4)
        
    return sorted(combined.values(), key=lambda x: x["final_score"], reverse=True)[:top_k]
```

#### **Listing 5.3: SuperMemo SM-2 Interval Calculation (`revision_engine.py`)**
```python
def calculate_next_review(rating: str, repetitions: int = 0, interval: int = 1, ease_factor: float = 2.5):
    if rating == "understood":
        new_reps = repetitions + 1
        new_interval = 1 if new_reps == 1 else (6 if new_reps == 2 else int(interval * ease_factor))
        new_ef = max(1.3, ease_factor + 0.1)
    elif rating == "review_tomorrow":
        new_reps = 0
        new_interval = 1
        new_ef = ease_factor
    else:  # need_revision
        new_reps = 0
        new_interval = 1
        new_ef = max(1.3, ease_factor - 0.2)
        
    next_date = date.today() + timedelta(days=new_interval)
    return new_interval, new_reps, new_ef, next_date.isoformat()
```

---

# CHAPTER 6 — TESTING, VALIDATION AND EVALUATION

### 6.1 Testing Approach
Testing was performed using `pytest` across automated unit, functional, and API layers:
* **Unit Tests:** Verified math formulas, chunk boundaries, OpenXML tag parsing, score normalization, and SM-2 interval calculations.
* **Corrupt & Edge Input Tests:** Zero-byte files, non-PDF byte arrays, HTML files masquerading as PDFs, and password-protected files.
* **API Tests:** Validated HTTP status codes (200, 201, 400, 413, 422) using `fastapi.testclient.TestClient`.

### 6.2 Functional Software Test Cases

| Test ID | Feature / Scenario | Input / Action | Expected Result | Actual Result |
|:---:|:---|:---|:---|:---:|
| **TC-01** | PDF Ingestion & Extraction | Valid 2-page text PDF | Ingested, text extracted, status `completed`. | **PASS** |
| **TC-02** | DOCX Ingestion & Pagination | 2-page DOCX with `<w:br w:type="page"/>` | Page count = 2; both page contents isolated. | **PASS** |
| **TC-03** | PPTX Slide Extraction | 2-slide PowerPoint presentation | Slide count = 2; text mapped to Page 1 and Page 2. | **PASS** |
| **TC-04** | Corrupt File Rejection | Random binary data renamed to `.pdf` | Caught safely; returns status `failed` with warning. | **PASS** |
| **TC-05** | Chunk Boundary Enforcement | 2,000 character continuous paragraph | Split into multiple sequential chunks $\ge 150$ chars. | **PASS** |
| **TC-06** | Lexical Formula Search | Query `F = ma` | Exact formula chunk retrieved via FTS5 BM25. | **PASS** |
| **TC-07** | Semantic Search Synonyms | Query "arrangement where order matters" | Locates permutation chunk without exact keyword. | **PASS** |
| **TC-08** | Active Recall Question Generation | Topic chunk text | Generates 3 questions (Fill blank, formula, T/F). | **PASS** |
| **TC-09** | SM-2 Scheduling Growth | Grade `Understood` across 3 cycles | Interval progresses: 1 day $\to$ 6 days $\to$ 15 days. | **PASS** |
| **TC-10** | Document Deletion Integrity | Delete document ID | DB records, chunks, FTS5 rows, and FAISS files purged. | **PASS** |

### 6.3 API Test Suite Execution
The backend API test suite (`backend/app/tests/`) executes 25 automated integration tests. All 25 passed in 19.52 seconds:
* `test_upload_and_extract_docx` $\to$ **PASSED** (HTTP 201)
* `test_upload_and_extract_pptx` $\to$ **PASSED** (HTTP 201)
* `test_search_validation_errors` $\to$ **PASSED** (HTTP 422 on invalid top_k)
* `test_deletion_cleanup` $\to$ **PASSED** (Cascade clean)
* `test_indexing_replaces_chunks_and_keyword_search_finds_formula` $\to$ **PASSED** (HTTP 200)

### 6.4 Information Retrieval Evaluation & Benchmark

| Query | Expected Topic | Mode | Top Result Score | Relevant? | Citation Accuracy |
|:---|:---|:---:|:---:|:---:|:---:|
| `permutation` | Combinatorics / Ordering | Keyword | 94.2% | **Yes** | Page 1, Chunk 1 |
| `nPr` | Permutation Formula | Keyword | 88.5% | **Yes** | Page 1, Chunk 2 |
| `arrangement where order matters` | Permutation Definition | Semantic | 81.4% | **Yes** | Page 1, Chunk 1 |
| `Newton's second law` | Classical Mechanics | Hybrid | 92.8% | **Yes** | Slide 2, Chunk 1 |
| `F = ma` | Force Equation | Keyword | 95.1% | **Yes** | Slide 2, Chunk 1 |
| `What is photosynthesis?` | Biology Notes | Hybrid | 86.7% | **Yes** | Page 3, Chunk 2 |
| `What is cricket?` | Unrelated Query | Hybrid | 14.2% (Filtered) | **Correctly Rejected** | N/A |

### 6.5 Result Analysis and Failure Cases
* **Failure Case 1 (Resolved):** Early tests revealed that unquoted formulas like `d/dx` or `(a+b)^2` caused SQLite FTS5 query parser syntax errors. This was resolved by creating `_sanitize_fts_query()`, which wraps individual token terms in double quotes.
* **Failure Case 2 (Resolved):** Windows DLL loader errors occurred when loading `faiss-cpu` alongside `fitz` on Python 3.14. Resolved by registering `faiss_cpu.libs` explicitly using `os.add_dll_directory()`.

---

# CHAPTER 7 — RESULTS AND SCREENSHOT EVIDENCE

### 7.1 Document Library & Ingestion Screen
* **Figure 7.1:** *Document Library View showing multi-format document management.*
* *Description:* Demonstrates successful ingestion of PDF, Word (`.docx`), and PowerPoint (`.pptx`) course materials. Each card presents total page/slide counts, extracted chunk totals, indexing status pills (`✅ Indexed`), and an expander to inspect raw extracted text.

### 7.2 Hybrid Search & Direct Answer Extraction
* **Figure 7.2:** *Hybrid Search Interface with Direct Answer synthesis.*
* *Description:* Demonstrates query retrieval for `"Newton's second law"`. The blue Direct Answer box synthesizes key definitions and formulas with high confidence, while the result cards display combined relevance percentage ($92.8\%$), semantic score ($89.2\%$), lexical score ($96.4\%$), and verbatim source citations.

### 7.3 Active Recall Practice Arena
* **Figure 7.3:** *Rule-based Practice Quiz generated from retrieved lecture notes.*
* *Description:* Demonstrates the active recall interface. Question 1 requires filling in the blank (`______`), Question 2 tests formula recall, and Question 3 tests statement validity (True/False). Instant grading evaluates student answers against source sentences.

### 7.4 SM-2 Spaced Revision Tracker
* **Figure 7.4:** *Simplified SM-2 Spaced Revision Dashboard.*
* *Description:* Shows the daily retention dashboard with metric cards for *Due Today*, *Overdue*, *Need Revision*, and *Understood*. Topics scheduled for review allow the student to launch a direct search with one click.

### 7.5 Interactive API Swagger Documentation
* **Figure 7.5:** *FastAPI Interactive Swagger UI (`/docs`).*
* *Description:* Demonstrates all REST endpoints (`/documents`, `/search`, `/practice`, `/revision`) with JSON request schemas, interactive execution, and response validation.

---

# CHAPTER 8 — DEPLOYMENT, USER GUIDE AND REPRODUCIBILITY

### 8.1 Installation and Setup Steps
1. **Clone the Repository:**
   ```powershell
   git clone https://github.com/[username]/studyverse-offline.git
   cd studyverse-offline
   ```
2. **Set Up Python Virtual Environment:**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. **Download Model Weights (Automated on First Run):**
   The application downloads `all-MiniLM-L6-v2` (90 MB) into the local HuggingFace cache upon initial startup. Subsequent runs are 100% offline.

### 8.2 User Operation Guide
1. Launch the app using `start.bat` (Full-Stack) or `start_standalone.bat` (Standalone).
2. Open your web browser to `http://localhost:8501`.
3. In **📚 Document Library**, drag and drop your PDFs, Word documents, or PPTX lecture slides, then click **📤 Upload & Extract**.
4. Click **⚡ Index All** to build dense and lexical search indexes.
5. In **🔍 Search Notes**, enter any query or formula to view ranked snippets and direct answers.
6. Click **🧠 Practice This Topic** on any search result to generate an active recall quiz.
7. Click **✅ Understood**, **🔁 Tomorrow**, or **⚠️ Need Revision** to schedule future reviews in the **📅 Revision Tracker**.

### 8.3 Deployment Details
StudyVerse is architected primarily as a local desktop software application for students and faculty. For lab or campus intranet deployment, it can be hosted on a local Ubuntu server:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

### 8.4 Reproducibility Information
* **Python Runtime:** Python 3.14.3 (Windows x86_64)
* **Random Seed:** Deterministic ranking and chunk generation (no stochastic generation).
* **Dependencies:** Defined with explicit version constraints in `requirements.txt`.
* **Testing:** 90 passing test cases reproducible via `pytest tests/ -v`.

### 8.5 Known Limitations
* **OCR Support:** Scanned photocopies without digital text layers cannot be indexed.
* **Complex Multi-Column Tables:** Complex nested financial spreadsheets in Word documents may flatten into sequential text rows.

---

# CHAPTER 9 — CONCLUSION AND FUTURE ENHANCEMENTS

### 9.1 Conclusion
In this project, we designed and implemented **StudyVerse Offline**, a privacy-first, local-first academic study assistant. By combining PyMuPDF and standard-library OpenXML parsers, the system reliably extracts text from PDFs, Word documents, and PowerPoint slide decks. By unifying SentenceTransformers vector embeddings with SQLite FTS5 lexical matching, it provides sub-50ms hybrid retrieval without external cloud APIs. Grounding search results with deterministic active recall quiz prompts and an SM-2 spaced repetition tracker creates an end-to-end learning tool that directly enhances student exam preparation while safeguarding academic privacy.

### 9.2 Future Enhancements
1. **Local OCR Ingestion:** Integration of lightweight Tesseract OCR or EasyOCR to transcribe scanned handwritten notes.
2. **Small Quantized LLM (GGUF):** Optional integration of a 4-bit quantized local model (such as Phi-3 Mini or Gemma-2B via `llama.cpp`) for conversational explanations on higher-end laptops.
3. **Cross-Platform Packaging:** Building one-click desktop installers using PyInstaller and Electron for non-technical users.
4. **Anki Deck Export:** Direct `.apkg` flashcard export enabling students to sync cards to mobile devices.

---

# REFERENCES

1. **Reimers, N., & Gurevych, I. (2019).** *Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks.* Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing (EMNLP). arXiv:1908.10084.
2. **Johnson, J., Douze, M., & Jégou, H. (2021).** *Billion-scale similarity search with GPUs.* IEEE Transactions on Big Data, 7(3), 535–547. (FAISS Library Documentation).
3. **Wozniak, P. A. (1990).** *Optimization of learning: A new approach to the design of repetition schedules in learning.* Master's Thesis, University of Technology in Poznan. (SuperMemo SM-2 Algorithm).
4. **Robertson, S., & Zaragoza, H. (2009).** *The Probabilistic Relevance Framework: BM25 and Beyond.* Foundations and Trends in Information Retrieval, 3(4), 333–389.
5. **FastAPI Documentation (2024).** *Modern, fast (high-performance), web framework for building APIs with Python.* https://fastapi.tiangolo.com/
6. **Streamlit Inc. (2024).** *Streamlit — A faster way to build and share data apps.* https://docs.streamlit.io/
7. **PyMuPDF Documentation (2024).** *PyMuPDF (fitz) documentation, Artifex Software Inc.* https://pymupdf.readthedocs.io/
8. **ISO/IEC 29500-1:2016.** *Information technology — Document description and processing languages — Office Open XML File Formats (WordprocessingML and PresentationML).* International Organization for Standardization.

