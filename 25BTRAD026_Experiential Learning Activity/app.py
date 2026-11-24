"""
StudyVerse AI Studio — Production Streamlit Application
======================================================
An offline-first, luxury AI study and document intelligence platform:
  • Executive Cockpit & Library — Multi-format ingestion (PDF, DOCX, PPTX) & indexing
  • Search Notes — Hybrid Neural FAISS + FTS5 BM25 search with verbatim AI synthesis
  • Practice Arena — Tactile 3D Flip-card quizzes with Anki deck export (.tsv)
  • Revision Hub — SuperMemo SM-2 Spaced Repetition engine for long-term retention
  • Progress & Analytics — Streak tracking, mastery curves, and retention metrics
  • Personal Notebook — Citations, TTS audio readout, bookmarks, and Markdown export

Backend: FastAPI at http://127.0.0.1:8000
"""
from __future__ import annotations

import os
import time
from io import BytesIO
from typing import Any

import requests
import streamlit as st
import streamlit.components.v1 as components

# ── Page configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="StudyVerse AI Studio",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded",
)

def _get_backend_url() -> str:
    # 1. Interactive sidebar override in current session
    if st.session_state.get("backend_url_override"):
        return st.session_state["backend_url_override"].strip().rstrip("/")
    # 2. Environment variable
    backend_url = os.getenv("BACKEND_URL")
    # 3. Streamlit secrets (on Streamlit Community Cloud)
    if not backend_url:
        try:
            backend_url = st.secrets.get("BACKEND_URL", "")
        except Exception:
            backend_url = ""
    # 4. Default to deployed Render backend
    if not backend_url:
        backend_url = "https://pythonexperiancial.onrender.com"
    return str(backend_url).strip().rstrip("/")


API_BASE = _get_backend_url()

# ═══════════════════════════════════════════════════════════════════
# SESSION STATE INITIALIZATION
# ═══════════════════════════════════════════════════════════════════
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "📜 Sepia"
if "current_revision_idx" not in st.session_state:
    st.session_state.current_revision_idx = 0
if "revision_queue" not in st.session_state:
    st.session_state.revision_queue = []
if "show_answer" not in st.session_state:
    st.session_state.show_answer = False
if "quiz_cards" not in st.session_state:
    st.session_state.quiz_cards = []
if "quiz_idx" not in st.session_state:
    st.session_state.quiz_idx = 0
if "quiz_show_answer" not in st.session_state:
    st.session_state.quiz_show_answer = False
if "quiz_score" not in st.session_state:
    st.session_state.quiz_score = 0
if "quiz_done" not in st.session_state:
    st.session_state.quiz_done = False
if "search_history" not in st.session_state:
    st.session_state.search_history = []
if "search_query_input" not in st.session_state:
    st.session_state.search_query_input = ""
if "notebook_entries" not in st.session_state:
    st.session_state.notebook_entries = []


# ═══════════════════════════════════════════════════════════════════
# THEME ENGINE — EXCLUSIVE ACADEMIC PARCHMENT / SEPIA PALETTE
# ═══════════════════════════════════════════════════════════════════
def get_theme_css(theme: str = "Sepia") -> str:
    # Exclusive Warm Academic Parchment & Espresso Theme
    vars_css = """
    :root {
        --sv-bg: #FBF0D9;
        --sv-bg-secondary: #F4E4C1;
        --sv-surface: #FFFDF8;
        --sv-surface-hover: #F8EFE0;
        --sv-border: #E6D7B8;
        --sv-border-focus: #B45309;

        --sv-primary: #B45309;
        --sv-primary-hover: #92400E;
        --sv-primary-glow: rgba(180, 83, 9, 0.22);
        --sv-secondary: #78350F;
        --sv-accent: #D97706;

        --sv-success: #15803D;
        --sv-success-bg: #DCFCE7;
        --sv-warning: #B45309;
        --sv-warning-bg: #FEF3C7;
        --sv-danger: #B91C1C;
        --sv-danger-bg: #FEE2E2;

        --sv-text-main: #3D2B1F;
        --sv-text-muted: #785A44;

        --sv-hero-bg: linear-gradient(135deg, #451A03 0%, #78350F 50%, #451A03 100%);
        --sv-card-front-bg: linear-gradient(135deg, #FFFDF8 0%, #F5EADB 100%);
        --sv-card-back-bg: linear-gradient(135deg, #FEF9C3 0%, #FEF08A 100%);
        --sv-card-front-text: #3D2B1F;
        --sv-card-back-text: #422006;
    }
    """

    # ── BASE REUSABLE ARCHITECTURE ──────────────────────────────────
    return vars_css + """
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    #MainMenu, footer, .stDeployButton {
        display: none !important;
    }

    .stApp {
        background-color: var(--sv-bg) !important;
        color: var(--sv-text-main) !important;
    }

    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2.5rem !important;
        max-width: 1260px !important;
    }

    /* ── Sidebar Overrides ── */
    [data-testid="stSidebar"] {
        background-color: var(--sv-bg-secondary) !important;
        border-right: 1px solid var(--sv-border) !important;
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label {
        color: var(--sv-text-main) !important;
    }

    /* ── Hero Banners ── */
    .sv-hero {
        background: var(--sv-hero-bg);
        border: 1px solid var(--sv-border);
        border-radius: 16px;
        padding: 2.2rem 2.5rem;
        margin-bottom: 1.8rem;
        color: #FFFFFF;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
        position: relative;
        overflow: hidden;
    }
    .sv-hero h1 {
        font-size: 2.2rem;
        font-weight: 800;
        margin: 0;
        color: #FFFFFF !important;
        letter-spacing: -0.02em;
    }
    .sv-hero p {
        font-size: 1.05rem;
        opacity: 0.88;
        margin: 0.4rem 0 0;
        color: #E2E8F0 !important;
        line-height: 1.5;
    }

    /* ── Bento & Metric Cards ── */
    .sv-metric {
        background-color: var(--sv-surface);
        border: 1px solid var(--sv-border);
        border-radius: 14px;
        padding: 1.3rem 1.5rem;
        text-align: center;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.2);
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .sv-metric:hover {
        transform: translateY(-2px);
        border-color: var(--sv-primary);
        box-shadow: 0 0 18px var(--sv-primary-glow);
    }
    .sv-metric .num {
        font-size: 2.3rem;
        font-weight: 800;
        color: var(--sv-accent);
        font-family: 'JetBrains Mono', monospace;
        line-height: 1.1;
    }
    .sv-metric .lbl {
        font-size: 0.82rem;
        font-weight: 600;
        color: var(--sv-text-muted);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-top: 0.4rem;
    }

    /* ── Section Titles ── */
    .sv-section-title {
        font-size: 1.18rem;
        font-weight: 700;
        color: var(--sv-text-main);
        border-bottom: 2px solid var(--sv-border);
        padding-bottom: 0.5rem;
        margin-bottom: 1.2rem;
        letter-spacing: -0.01em;
    }

    /* ── Status Pills & Badges ── */
    .pill, .sv-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 0.22rem 0.8rem;
        border-radius: 9999px;
        font-size: 0.76rem;
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
    }
    .pill-green  { background: var(--sv-success-bg); color: var(--sv-success); border: 1px solid var(--sv-success); }
    .pill-amber  { background: var(--sv-warning-bg); color: var(--sv-warning); border: 1px solid var(--sv-warning); }
    .pill-red    { background: var(--sv-danger-bg);  color: var(--sv-danger);  border: 1px solid var(--sv-danger); }
    .pill-blue   { background: rgba(37, 99, 235, 0.15); color: #60A5FA; border: 1px solid rgba(96, 165, 250, 0.4); }
    .pill-gray   { background: rgba(148, 163, 184, 0.15); color: var(--sv-text-muted); border: 1px solid var(--sv-border); }
    .pill-accent { background: var(--sv-primary-glow); color: var(--sv-accent); border: 1px solid var(--sv-accent); }

    /* ── Streak Badge ── */
    .streak-badge {
        background: linear-gradient(135deg, #F97316 0%, #EA580C 50%, #C2410C 100%);
        color: #FFFFFF;
        border-radius: 14px;
        padding: 1.2rem 1.8rem;
        text-align: center;
        font-size: 2.1rem;
        font-weight: 800;
        box-shadow: 0 6px 20px rgba(234, 88, 12, 0.35);
    }
    .streak-badge small {
        display: block;
        font-size: 0.85rem;
        font-weight: 500;
        opacity: 0.92;
        margin-top: 0.3rem;
    }

    /* ── Direct Answer Synthesis Box ── */
    .sv-answer-box {
        background-color: var(--sv-surface);
        border: 1px solid var(--sv-border);
        border-left: 6px solid var(--sv-accent);
        border-radius: 14px;
        padding: 1.6rem 2rem;
        margin-bottom: 1.6rem;
        box-shadow: 0 0 24px var(--sv-primary-glow);
    }
    .sv-answer-box .title {
        font-size: 0.82rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: var(--sv-accent);
        margin-bottom: 0.6rem;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .sv-answer-box .direct-text {
        font-size: 1.18rem;
        font-weight: 600;
        line-height: 1.65;
        color: var(--sv-text-main);
        margin-bottom: 0.8rem;
    }
    .sv-answer-box .keypoint-item {
        font-size: 0.96rem;
        color: var(--sv-text-muted);
        line-height: 1.55;
        margin: 0.4rem 0;
        padding-left: 0.5rem;
    }
    .sv-answer-box .meta {
        font-size: 0.82rem;
        color: var(--sv-text-muted);
        margin-top: 0.9rem;
        padding-top: 0.6rem;
        border-top: 1px dashed var(--sv-border);
    }

    /* ── Search Results & Document Cards ── */
    .sv-result, .sv-search-card {
        background-color: var(--sv-surface);
        border: 1px solid var(--sv-border);
        border-radius: 14px;
        padding: 1.3rem 1.6rem;
        margin-bottom: 1.1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.18);
        transition: all 0.22s ease-in-out;
    }
    .sv-result:hover, .sv-search-card:hover {
        border-color: var(--sv-primary);
        box-shadow: 0 4px 18px var(--sv-primary-glow);
        transform: translateY(-1px);
    }
    .sv-result .rank {
        font-size: 0.72rem;
        font-weight: 700;
        color: var(--sv-accent);
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
    .sv-result .score {
        font-size: 0.88rem;
        font-weight: 600;
        color: var(--sv-primary);
        margin-top: 0.2rem;
    }
    .sv-result .text {
        font-size: 0.96rem;
        line-height: 1.7;
        color: var(--sv-text-main);
        margin: 0.6rem 0;
    }
    .sv-result .cite {
        font-size: 0.82rem;
        color: var(--sv-text-muted);
    }

    /* ── 3D Interactive Flip Card ── */
    .flip-card-container {
        perspective: 1200px;
        margin: 1.5rem 0 1.8rem 0;
        width: 100%;
        cursor: pointer;
    }
    .flip-card {
        width: 100%;
        min-height: 260px;
        position: relative;
        transform-style: preserve-3d;
        transition: transform 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
        border-radius: 18px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
    }
    .flip-card.is-flipped {
        transform: rotateY(180deg);
    }
    .flip-card-front, .flip-card-back {
        position: absolute;
        top: 0; left: 0;
        width: 100%;
        height: 100%;
        min-height: 260px;
        backface-visibility: hidden;
        -webkit-backface-visibility: hidden;
        border-radius: 18px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        padding: 2.2rem 2.8rem;
        box-sizing: border-box;
        text-align: center;
        border: 1px solid var(--sv-border);
    }
    .flip-card-front {
        background: var(--sv-card-front-bg);
        color: var(--sv-card-front-text);
        transform: rotateY(0deg);
    }
    .flip-card-back {
        background: var(--sv-card-back-bg);
        color: var(--sv-card-back-text);
        transform: rotateY(180deg);
        border-color: rgba(16, 185, 129, 0.35);
    }
    .flip-card .label {
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.09em;
        text-transform: uppercase;
        margin-bottom: 0.9rem;
        color: var(--sv-accent);
    }
    .flip-card .qtext {
        font-size: 1.32rem;
        font-weight: 700;
        line-height: 1.55;
    }
    .flip-card .atext {
        font-size: 1.18rem;
        font-weight: 500;
        line-height: 1.65;
    }
    .flip-hint {
        font-size: 0.82rem;
        opacity: 0.75;
        margin-top: 1.2rem;
        color: var(--sv-text-muted);
    }
    .flip-meta {
        font-size: 0.8rem;
        opacity: 0.85;
        margin-top: 0.9rem;
    }

    /* ── Notebook Cards ── */
    .notebook-card {
        background-color: var(--sv-surface);
        border: 1px solid var(--sv-border);
        border-radius: 14px;
        padding: 1.3rem 1.6rem;
        margin-bottom: 1.1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.18);
        transition: all 0.22s ease;
    }
    .notebook-card:hover {
        border-color: var(--sv-primary);
        box-shadow: 0 4px 16px var(--sv-primary-glow);
    }

    /* ── Streamlit Form & Controls Overrides ── */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > div,
    .stTextArea > div > div > textarea {
        background-color: var(--sv-surface) !important;
        color: var(--sv-text-main) !important;
        border: 1px solid var(--sv-border) !important;
        border-radius: 10px !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--sv-border-focus) !important;
        box-shadow: 0 0 0 2px var(--sv-primary-glow) !important;
    }

    .stButton > button {
        background: linear-gradient(135deg, var(--sv-primary) 0%, var(--sv-secondary) 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        padding: 0.5rem 1.3rem !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2) !important;
    }
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 16px var(--sv-primary-glow) !important;
    }
    .stButton > button:active {
        transform: translateY(1px) !important;
    }

    /* Progress bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, var(--sv-primary), var(--sv-accent)) !important;
        border-radius: 9999px !important;
    }
    """


# ═══════════════════════════════════════════════════════════════════
# API CLIENT — thin wrapper
# ═══════════════════════════════════════════════════════════════════
def _safe_json(r: requests.Response | None, default: Any = None) -> Any:
    if r is None:
        return default
    try:
        return r.json()
    except (requests.exceptions.JSONDecodeError, ValueError):
        return default


def _get(path: str, **kwargs) -> requests.Response | None:
    api_base = _get_backend_url()
    try:
        return requests.get(f"{api_base}{path}", timeout=25, **kwargs)
    except requests.exceptions.RequestException:
        return None


def _post(path: str, **kwargs) -> requests.Response | None:
    api_base = _get_backend_url()
    try:
        return requests.post(f"{api_base}{path}", timeout=90, **kwargs)
    except requests.exceptions.RequestException:
        return None


def _delete(path: str, **kwargs) -> requests.Response | None:
    api_base = _get_backend_url()
    try:
        return requests.delete(f"{api_base}{path}", timeout=25, **kwargs)
    except requests.exceptions.RequestException:
        return None


def backend_online() -> bool:
    r = _get("/health")
    if r is None or r.status_code != 200:
        return False
    data = _safe_json(r)
    return isinstance(data, dict) and data.get("status") == "ok"


def api_list_documents() -> list[dict]:
    r = _get("/documents")
    if r is None:
        st.error(f"Could not connect to backend at `{_get_backend_url()}`. If on Render free tier, it may be waking up.")
        return []
    if r.status_code != 200:
        st.error(f"Backend returned HTTP {r.status_code} for /documents. Check FastAPI logs.")
        return []
    data = _safe_json(r)
    if data is None:
        content_type = r.headers.get("Content-Type", "unknown")
        st.error(
            f"Backend returned non-JSON for /documents (Content-Type: {content_type}). "
            f"Verify BACKEND_URL (`{_get_backend_url()}`) points to FastAPI, not Streamlit."
        )
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("documents"), list):
        return data["documents"]
    st.error("The backend returned an unexpected response for /documents; expected a JSON list.")
    return []


def _get_mime_type(filename: str) -> str:
    lower = filename.lower()
    if lower.endswith(".docx"):
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    if lower.endswith(".pptx"):
        return "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    if lower.endswith(".doc"):
        return "application/msword"
    if lower.endswith(".ppt"):
        return "application/vnd.ms-powerpoint"
    return "application/pdf"


def api_upload_documents(files: list) -> list[dict]:
    file_tuples = [("files", (f.name, f.read(), _get_mime_type(f.name))) for f in files]
    r = _post("/documents/upload", files=file_tuples)
    if r and r.status_code in (200, 201):
        data = _safe_json(r, {})
        return data if isinstance(data, list) else data.get("results", [])
    data = _safe_json(r, {})
    msg = data.get("detail", f"Upload failed (HTTP {r.status_code})") if r else "Backend offline"
    st.error(f"Upload error: {msg}")
    return []


def api_index_document(doc_id: int) -> dict | None:
    r = _post(f"/documents/{doc_id}/index", json={})
    if r and r.status_code == 200:
        return _safe_json(r, {})
    data = _safe_json(r, {})
    msg = data.get("detail", f"Indexing failed (HTTP {r.status_code})") if r else "Backend offline"
    st.error(f"Indexing error: {msg}")
    return None


def api_index_all() -> dict | None:
    r = _post("/documents/index-all", json={})
    if r and r.status_code == 200:
        return _safe_json(r, {})
    data = _safe_json(r, {})
    msg = data.get("detail", f"Index-all failed (HTTP {r.status_code})") if r else "Backend offline"
    st.error(f"Index-all error: {msg}")
    return None


def api_delete_document(doc_id: int) -> bool:
    r = _delete(f"/documents/{doc_id}")
    if r and r.status_code == 200:
        body = _safe_json(r, {})
        if body.get("cleanup_complete", True):
            return True
        details = "; ".join(body.get("cleanup_errors", [])) or body.get("message", "Cleanup incomplete")
        st.error(f"Delete incomplete: {details}")
        return False
    data = _safe_json(r, {})
    msg = data.get("detail", f"Delete failed (HTTP {r.status_code})") if r else "Backend offline"
    st.error(f"Delete error: {msg}")
    return False


def api_get_pages(doc_id: int) -> list[dict]:
    r = _get(f"/documents/{doc_id}/pages")
    if r and r.status_code == 200:
        data = _safe_json(r, [])
        return data if isinstance(data, list) else data.get("pages", [])
    return []


def api_search(query: str, mode: str, doc_ids: list[int], top_k: int, min_score: float) -> dict | None:
    r = _post("/search", json={
        "query": query.strip(),
        "mode": mode,
        "document_ids": doc_ids,
        "top_k": top_k,
        "min_score": min_score,
        "include_debug": False,
    })
    if r and r.status_code == 200:
        return _safe_json(r)
    data = _safe_json(r, {})
    if r and r.status_code == 422:
        details = data.get("detail", "Validation error")
        st.error(f"Search validation error: {details}")
    elif r:
        msg = data.get("detail", f"Search failed (HTTP {r.status_code})")
        st.error(f"Search error: {msg}")
    else:
        st.error("Backend offline. Check connection to FastAPI backend.")
    return None


def api_get_progress() -> dict | None:
    r = _get("/progress/summary")
    if r and r.status_code == 200:
        return _safe_json(r)
    return None


def api_get_due_cards(limit: int = 50) -> list[dict]:
    r = _get(f"/revision/due?limit={limit}")
    if r and r.status_code == 200:
        data = _safe_json(r, [])
        return data if isinstance(data, list) else []
    return []


def api_review_card(card_id: int, quality: int) -> dict | None:
    r = _post(f"/revision/review/{card_id}", json={"quality": quality})
    if r and r.status_code == 200:
        return _safe_json(r)
    return None


def api_generate_cards(doc_ids: list[int], max_per_doc: int = 10) -> dict | None:
    r = _post("/practice/generate", json={"document_ids": doc_ids, "max_cards_per_doc": max_per_doc})
    if r and r.status_code == 200:
        return _safe_json(r)
    data = _safe_json(r, {})
    msg = data.get("detail", f"Card generation failed (HTTP {r.status_code})") if r else "Backend offline"
    st.error(f"Practice error: {msg}")
    return None


def api_list_flashcards(doc_id: int | None = None) -> list[dict]:
    url = "/practice/flashcards"
    if doc_id:
        url += f"?document_id={doc_id}"
    r = _get(url)
    if r and r.status_code == 200:
        data = _safe_json(r, [])
        return data if isinstance(data, list) else []
    return []


def api_delete_flashcard(card_id: int) -> bool:
    r = _delete(f"/practice/flashcards/{card_id}")
    return r is not None and r.status_code == 200


# ═══════════════════════════════════════════════════════════════════
# PRODUCTIVITY HELPERS (Anki, Study Guide, TTS, Notebook)
# ═══════════════════════════════════════════════════════════════════
def generate_anki_tsv(cards: list[dict]) -> str:
    """Generates TSV format ready for direct import into Anki."""
    lines = ["#separator:tab", "#html:true", "#tags column:3"]
    for c in cards:
        q = c.get("question", "").replace("\t", " ").replace("\n", "<br>")
        a = c.get("answer", "").replace("\t", " ").replace("\n", "<br>")
        ctx = c.get("context", "")
        if ctx:
            a += f"<br><br><b>Context:</b> <i>{ctx[:180]}...</i>"
        doc_id = c.get("document_id", "general")
        page = c.get("page_number", "")
        tag = f"StudyVerse doc_{doc_id}"
        if page:
            tag += f" page_{page}"
        lines.append(f"{q}\t{a}\t{tag}")
    return "\n".join(lines)


def generate_study_guide_markdown(query: str, result: dict) -> str:
    """Compiles search query results, direct answer, and citations into Markdown."""
    now_str = time.strftime("%Y-%m-%d %H:%M")
    lines = [
        f"# 📚 StudyVerse Revision Sheet: {query}",
        f"*Generated on {now_str} via StudyVerse AI Studio*",
        "",
        "---",
    ]
    direct_ans = result.get("direct_answer")
    if direct_ans and direct_ans.get("direct_answer"):
        lines.extend([
            "## 💡 Direct Synthesis (Verbatim Anchor)",
            f"> {direct_ans.get('direct_answer')}",
            "",
        ])
        key_pts = direct_ans.get("key_points", [])
        if key_pts:
            lines.append("### Key Takeaways")
            for pt in key_pts:
                lines.append(f"- {pt}")
            lines.append("")
        src_file = direct_ans.get("primary_source_filename", "")
        src_page = direct_ans.get("primary_source_page", "")
        if src_file:
            lines.append(f"**Primary Citation:** `{src_file}` (Page {src_page})")
            lines.append("")
        lines.append("---")

    lines.append("## 📖 Retrieved Source Extracts")
    for r in result.get("results", []):
        score_pct = r.get("final_score_percent", 0.0)
        lines.extend([
            f"### Result #{r.get('rank')} · Relevance: {score_pct:.1f}%",
            f"**File:** `{r.get('filename')}` | **Page:** {r.get('page_number')} | **Chunk:** {r.get('chunk_number')}",
            "",
            f"```\n{r.get('text')}\n```",
            "",
        ])
    return "\n".join(lines)


def render_tts_button(text: str, label: str = "🔊 Read Aloud", button_id: str = "tts_btn"):
    """Injects a Web Speech API button into the page."""
    safe_text = (
        text.replace('"', '\\"')
        .replace("'", "\\'")
        .replace("\n", " ")
        .replace("\r", "")
    )
    html_code = f"""
    <div style="margin: 0.35rem 0;">
        <button id="{button_id}" onclick="speak_{button_id}()" style="
            background: linear-gradient(135deg, #B45309 0%, #78350F 100%);
            color: #FFFDF8; border: 1px solid #92400E; border-radius: 8px;
            padding: 6px 14px; font-size: 0.82rem; font-weight: 600; cursor: pointer;
            display: inline-flex; align-items: center; gap: 6px; box-shadow: 0 2px 6px rgba(120,53,15,0.2);
            transition: all 0.2s ease;
        " onmouseover="this.style.transform='translateY(-1px)'" onmouseout="this.style.transform='translateY(0)'">
            {label}
        </button>
        <span id="{button_id}_status" style="font-size: 0.75rem; color: #785A44; margin-left: 8px;"></span>
    </div>
    <script>
    function speak_{button_id}() {{
        if (!('speechSynthesis' in window)) {{
            alert('Text-to-speech is not supported by your browser.');
            return;
        }}
        const synth = window.speechSynthesis;
        const status = document.getElementById('{button_id}_status');
        if (synth.speaking) {{
            synth.cancel();
            status.textContent = '⏹️ Stopped';
            setTimeout(() => {{ status.textContent = ''; }}, 1500);
            return;
        }}
        const utter = new SpeechSynthesisUtterance("{safe_text}");
        utter.rate = 1.0;
        utter.pitch = 1.0;
        status.textContent = '▶️ Speaking...';
        utter.onend = function() {{ status.textContent = ''; }};
        utter.onerror = function() {{ status.textContent = ''; }};
        synth.speak(utter);
    }}
    </script>
    """
    components.html(html_code, height=45)


def add_to_notebook(title: str, text: str, source: str = "", category: str = "Citation"):
    """Adds an entry to user's personal notebook."""
    st.session_state.notebook_entries.append({
        "id": int(time.time() * 1000),
        "title": title,
        "text": text,
        "source": source,
        "category": category,
        "date": time.strftime("%Y-%m-%d %H:%M"),
    })


def export_notebook_markdown() -> str:
    """Exports all notebook entries to Markdown."""
    now_str = time.strftime("%Y-%m-%d %H:%M")
    lines = [
        "# 📓 StudyVerse Personal Notebook",
        f"*Exported on {now_str}*",
        "",
        "---",
        "",
    ]
    for idx, item in enumerate(st.session_state.notebook_entries, 1):
        lines.append(f"## {idx}. {item['title']} [{item['category']}]")
        lines.append(f"*Saved: {item['date']}*")
        if item.get("source"):
            lines.append(f"**Source:** {item['source']}")
        lines.append("")
        lines.append(f"{item['text']}")
        lines.append("")
        lines.append("---")
        lines.append("")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
# GENERAL UI HELPERS
# ═══════════════════════════════════════════════════════════════════
def status_pill(status: str) -> str:
    mapping = {
        "completed": ("pill-green", "✅ Indexed"),
        "pending":   ("pill-gray",  "⏳ Pending"),
        "warning":   ("pill-amber", "⚠️ Warning"),
        "failed":    ("pill-red",   "❌ Failed"),
    }
    css, label = mapping.get(status, ("pill-gray", status.title()))
    return f'<span class="pill {css}">{label}</span>'


def score_color(pct: float) -> str:
    if pct >= 70: return "🟢"
    if pct >= 40: return "🟡"
    return "🔴"


def metric_card(col, num, label, pill: str = ""):
    pill_html = f'<span class="pill pill-accent" style="margin-bottom:0.3rem;">{pill}</span>' if pill else ""
    col.markdown(f"""
        <div class="sv-metric">
            {pill_html}
            <div class="num">{num}</div>
            <div class="lbl">{label}</div>
        </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# SIDEBAR NAVIGATION & TELEMETRY
# ═══════════════════════════════════════════════════════════════════
with st.sidebar:
    online = backend_online()
    status_indicator = "🟢" if online else "🔴"
    status_text = "FastAPI Online" if online else "FastAPI Offline"

    st.markdown("""
    <div style="padding: 0.4rem 0 0.8rem 0;">
        <div style="font-size: 1.45rem; font-weight: 800; letter-spacing: -0.02em; background: linear-gradient(135deg, #B45309 0%, #D97706 50%, #78350F 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            📜 STUDYVERSE
        </div>
        <div style="font-size: 0.74rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; color: #785A44;">
            AI Academic OS · Local Intelligence
        </div>
    </div>
    """, unsafe_allow_html=True)

    active_url = _get_backend_url()
    st.markdown(f"""
    <div style="background: {'rgba(21, 128, 61, 0.12)' if online else 'rgba(185, 28, 28, 0.12)'};
                border: 1px solid {'rgba(21, 128, 61, 0.35)' if online else 'rgba(185, 28, 28, 0.35)'};
                border-radius: 12px; padding: 0.8rem 1rem; margin-bottom: 0.8rem;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <strong style="color: {'#15803D' if online else '#B91C1C'};">{status_indicator} {status_text}</strong>
            <span style="font-size:0.72rem; font-family:'JetBrains Mono'; color:#785A44;">FastAPI</span>
        </div>
        <div style="color: #785A44; font-size: 0.72rem; margin-top: 4px; word-break: break-all; font-family: 'JetBrains Mono', monospace;">
            {active_url}
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not online:
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("🔄 Wake / Test", use_container_width=True):
                st.rerun()
        with col_btn2:
            toggle_settings = st.checkbox("⚙️ Config", value=False)
        
        if toggle_settings:
            custom_url = st.text_input("Backend API URL", value=active_url, key="input_custom_backend")
            if st.button("Connect URL", use_container_width=True):
                st.session_state["backend_url_override"] = custom_url
                st.rerun()
        
        st.caption("⏳ *Render free tier may take ~30-40s to wake from cold sleep. Click **Wake / Test** to retry.*")

    st.markdown("<small style='color: #785A44; font-weight:700; text-transform:uppercase; letter-spacing:0.08em;'>Navigation</small>", unsafe_allow_html=True)

    page = st.radio(
        "Navigate",
        ["📚 Library", "🔍 Search Notes", "🎯 Practice Arena", "🔁 Revision Hub", "📈 Progress", "📓 Notebook"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown(f"""
    <div style="font-size: 0.78rem; color: #785A44; line-height: 1.5;">
        <div>💾 <b>{len(st.session_state.notebook_entries)}</b> notes in Notebook</div>
        <div style="margin-top: 6px;">🔒 <b>100% Offline & Private</b></div>
        <div style="font-size: 0.72rem; opacity: 0.85; color: #785A44;">Zero cloud telemetry · Local CPU FAISS</div>
    </div>
    """, unsafe_allow_html=True)

# Apply custom CSS based on selected theme
st.markdown(f"<style>{get_theme_css(st.session_state.theme_mode)}</style>", unsafe_allow_html=True)

# Inject Spacebar key listener for 3D flip card
components.html("""
<script>
(function() {
    const parentDoc = window.parent.document;
    if (!parentDoc._sv_space_listener_bound) {
        parentDoc._sv_space_listener_bound = true;
        parentDoc.addEventListener('keydown', function(e) {
            if (e.target && (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA')) return;
            if (e.code === 'Space') {
                const card = parentDoc.querySelector('.flip-card');
                if (card) {
                    e.preventDefault();
                    card.classList.toggle('is-flipped');
                }
            }
        });
    }
})();
</script>
""", height=0, width=0)


# ═══════════════════════════════════════════════════════════════════
# PAGE: LIBRARY (Executive Cockpit & Document Management)
# ═══════════════════════════════════════════════════════════════════
if page == "📚 Library":
    st.markdown("""
    <div class="sv-hero">
        <span class="pill pill-accent" style="margin-bottom:0.7rem;">⚡ Offline Neural Intelligence</span>
        <h1>📚 Document Library & Executive Cockpit</h1>
        <p>Ingest and manage PDF, Word (.docx), and PowerPoint (.pptx) documents. All text is chunked and embedded locally using all-MiniLM-L6-v2.</p>
    </div>
    """, unsafe_allow_html=True)

    docs = api_list_documents()
    indexed_docs = [d for d in docs if d.get("is_indexed")]
    total_chunks = sum(d.get("chunks_count", 0) for d in docs)

    # ── Executive Bento Cockpit ──
    b1, b2, b3, b4 = st.columns(4)
    metric_card(b1, len(docs), "Total Documents", pill="Library")
    metric_card(b2, len(indexed_docs), "Indexed Documents", pill="Searchable")
    metric_card(b3, total_chunks, "Semantic Chunks", pill="Embedded")
    metric_card(b4, "Sub-50ms", "Local Retrieval", pill="FAISS-CPU")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Upload panel ──
    with st.expander("➕ Upload Documents (PDF, Word .docx, PowerPoint .pptx)", expanded=not docs):
        uploaded = st.file_uploader(
            "Drop PDF, Word (.docx), or PowerPoint (.pptx) files here",
            type=["pdf", "docx", "pptx", "doc", "ppt"],
            accept_multiple_files=True,
            help="Upload text-based PDF, Word (.docx, .doc), or PowerPoint (.pptx, .ppt) documents.",
        )
        col_upload, col_idx_all = st.columns([1, 1])
        if col_upload.button("📤 Upload Documents", type="primary", disabled=not uploaded or not online):
            with st.spinner("Extracting and segmenting text…"):
                results = api_upload_documents(list(uploaded))
            if results:
                ok = sum(1 for r in results if r.get("extraction_status") == "completed")
                warn = sum(1 for r in results if r.get("extraction_status") == "warning")
                st.success(f"✅ Ingested {ok} document(s)." + (f" ⚠️ {warn} scanned or low text." if warn else ""))
                st.rerun()

        if col_idx_all.button("⚡ Index All Unindexed Docs", disabled=not online or not docs):
            with st.spinner("Generating dense vectors and building FAISS indexes…"):
                result = api_index_all()
            if result:
                st.success(f"✅ Indexed {result.get('indexed_document_count', 0)} document(s). Chunks generated: {result.get('total_chunks_created', 0)}")
                st.rerun()

    # ── Documents Management List ──
    st.markdown('<div class="sv-section-title">Your Knowledge Vault</div>', unsafe_allow_html=True)

    if not docs:
        st.info("📭 Your library is currently empty. Upload a PDF, Word, or PowerPoint file above to start indexing.")
    else:
        for doc in docs:
            doc_id = doc["id"]
            filename = doc["filename"]
            chunks = doc.get("chunks_count", 0)
            pages = doc.get("page_count", 0)
            extraction_status = doc.get("extraction_status", "pending")
            is_indexed = doc.get("is_indexed", False)
            display_status = "completed" if is_indexed else extraction_status

            # File format icon
            ext = filename.split(".")[-1].lower() if "." in filename else "pdf"
            format_icon = "📊 PPTX" if "ppt" in ext else ("📝 DOCX" if "doc" in ext else "📄 PDF")

            with st.container():
                c1, c2, c3, c4, c5 = st.columns([3.5, 1.8, 2.2, 1.2, 1.3])
                c1.markdown(f"**{filename}**<br><span style='font-size:0.75rem; color:#94A3B8;'>{format_icon} · Doc #{doc_id}</span>", unsafe_allow_html=True)
                c2.markdown(status_pill(display_status), unsafe_allow_html=True)
                c3.markdown(f"<span style='font-family:\"JetBrains Mono\"; font-size:0.85rem;'>{pages} pgs · {chunks} chunks</span>", unsafe_allow_html=True)

                with c4:
                    if st.button("⚡ Index", key=f"idx_{doc_id}", disabled=not online or extraction_status != "completed"):
                        with st.spinner(f"Indexing {filename}…"):
                            result = api_index_document(doc_id)
                        if result:
                            st.success(f"✅ {result.get('chunks_created', 0)} chunks indexed")
                            st.rerun()

                with c5:
                    if st.button("🗑️ Delete", key=f"del_{doc_id}", help="Delete document and related indexes", disabled=not online):
                        with st.spinner("Deleting…"):
                            ok = api_delete_document(doc_id)
                        if ok:
                            st.success("Deleted")
                            st.rerun()

                # Text Inspector expander
                if is_indexed:
                    with st.expander(f"📖 Inspect extracted content — {filename}"):
                        pages_data = api_get_pages(doc_id)
                        if pages_data:
                            page_sel = st.selectbox(
                                "Select page to view text",
                                [p["page_number"] for p in pages_data],
                                key=f"psel_{doc_id}",
                            )
                            for p in pages_data:
                                if p["page_number"] == page_sel:
                                    st.text_area(
                                        f"Page {page_sel} verbatim stream",
                                        value=p.get("text", ""),
                                        height=220,
                                        key=f"ptxt_{doc_id}_{page_sel}",
                                        label_visibility="collapsed",
                                    )
                st.divider()


# ═══════════════════════════════════════════════════════════════════
# PAGE: SEARCH NOTES (Hybrid Neural FAISS + FTS5 BM25)
# ═══════════════════════════════════════════════════════════════════
elif page == "🔍 Search Notes":
    st.markdown("""
    <div class="sv-hero">
        <span class="pill pill-accent" style="margin-bottom:0.7rem;">🎯 100% Hallucination-Free</span>
        <h1>🔍 Semantic & Hybrid Search Notes</h1>
        <p>Query your academic corpus using natural language. Retrieves exact verbatim source paragraphs with page-level citations and direct synthesis.</p>
    </div>
    """, unsafe_allow_html=True)

    docs = api_list_documents()
    indexed_docs = [d for d in docs if d.get("is_indexed")]

    # ── Search suggestion & history chips ──
    if st.session_state.search_history:
        st.markdown("<small style='color: #94A3B8;'>🕒 <b>Recent Searches:</b></small>", unsafe_allow_html=True)
        h_cols = st.columns(min(len(st.session_state.search_history[:5]), 5))
        for h_idx, h_text in enumerate(st.session_state.search_history[:5]):
            if h_cols[h_idx].button(f"🔍 {h_text[:22]}", key=f"h_btn_{h_idx}"):
                st.session_state.search_query_input = h_text
                st.rerun()

    suggested_templates = ["Key Definitions", "System Architecture", "Algorithms & Steps", "Formulas & Equations", "Summary Overview"]
    st.markdown("<small style='color: #94A3B8;'>💡 <b>Quick Concept Templates:</b></small>", unsafe_allow_html=True)
    s_cols = st.columns(len(suggested_templates))
    for s_idx, s_text in enumerate(suggested_templates):
        if s_cols[s_idx].button(s_text, key=f"s_btn_{s_idx}"):
            st.session_state.search_query_input = s_text
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    col_q, col_mode = st.columns([3, 1])
    query = col_q.text_input(
        "Ask a study question or search term:",
        value=st.session_state.search_query_input,
        placeholder="e.g. What is virtual memory? or explain page replacement algorithms",
        key="search_query_main_input",
    )
    mode = col_mode.selectbox(
        "Search Mode",
        ["hybrid", "semantic", "keyword"],
        format_func=lambda x: {"hybrid": "🔀 Hybrid (FAISS + BM25)", "semantic": "🧠 Semantic (Dense)", "keyword": "🔑 Keyword (FTS5)"}.get(x, x),
    )

    col_k, col_score = st.columns(2)
    top_k = col_k.slider("Results to show (Top-K)", 1, 10, 5)
    min_score = col_score.slider("Minimum relevance (0 = show all)", 0.0, 1.0, 0.0, 0.05)

    st.markdown("**🗂️ Search Scope (Indexed Documents):**")
    if not indexed_docs:
        st.warning("⚠️ No indexed documents available. Go to Library → Click '⚡ Index' on an uploaded file first.")
        selected_ids = []
    else:
        col_sel_all, _ = st.columns([1, 4])
        if col_sel_all.button("Select All"):
            for d in indexed_docs:
                st.session_state[f"doc_chk_{d['id']}"] = True

        doc_cols = st.columns(min(len(indexed_docs), 4))
        selected_ids = []
        for i, d in enumerate(indexed_docs):
            key = f"doc_chk_{d['id']}"
            if key not in st.session_state:
                st.session_state[key] = True
            checked = doc_cols[i % 4].checkbox(d["filename"], key=key)
            if checked:
                selected_ids.append(d["id"])

    search_btn = st.button("🔍 Run Semantic Search", type="primary", disabled=not query.strip() or not selected_ids or not online)

    if search_btn:
        clean_q = query.strip()
        if clean_q and (not st.session_state.search_history or st.session_state.search_history[0] != clean_q):
            st.session_state.search_history.insert(0, clean_q)
            st.session_state.search_history = st.session_state.search_history[:8]

        with st.spinner("Scanning dense vector space & lexical indexes…"):
            result = api_search(clean_q, mode, selected_ids, top_k, min_score)

        if result:
            results = result.get("results", [])
            st.markdown("---")
            n = len(results)
            filtered = result.get("filtered_by_min_score", False)

            if filtered:
                st.warning("⚠️ Matches were found, but none met your minimum relevance threshold. Lower the slider to inspect them.")
            elif n == 0:
                st.info("🔍 No matching passages found. Try different keywords or index more documents.")
            else:
                # ── Download Study Guide Button ──
                guide_md = generate_study_guide_markdown(clean_q, result)
                q_slug = "".join([c if c.isalnum() else "_" for c in clean_q[:25]]).strip("_")
                st.download_button(
                    label="📄 Download Revision Sheet (.md)",
                    data=guide_md,
                    file_name=f"study_guide_{q_slug}.md",
                    mime="text/markdown",
                    help="Export this direct answer and all source extracts to a Markdown revision sheet.",
                )

                # ── Direct Answer Synthesis at Top ──
                direct_ans = result.get("direct_answer")
                if direct_ans and direct_ans.get("direct_answer"):
                    ans_text = direct_ans.get("direct_answer")
                    key_pts = direct_ans.get("key_points", [])
                    src_page = direct_ans.get("primary_source_page")
                    src_file = direct_ans.get("primary_source_filename")
                    conf = direct_ans.get("confidence", "medium").upper()

                    points_html = ""
                    if key_pts:
                        points_html = "<div style='margin-top: 0.6rem;'>" + "".join([f"<div class='keypoint-item'>• {pt}</div>" for pt in key_pts]) + "</div>"

                    meta_info = f"Source Citation: <strong>{src_file}</strong> (Page {src_page}) &nbsp;·&nbsp; Verification Confidence: {conf}" if src_file else ""

                    st.markdown(f"""
                    <div class="sv-answer-box">
                        <div class="title">✨ AI Direct Synthesis (Verbatim Anchor)</div>
                        <div class="direct-text">"{ans_text}"</div>
                        {points_html}
                        <div class="meta">{meta_info}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    ans_col1, ans_col2 = st.columns([1, 1])
                    with ans_col1:
                        render_tts_button(ans_text, label="🔊 Read Direct Answer", button_id="tts_direct_ans")
                    with ans_col2:
                        if st.button("⭐ Save Direct Answer to Notebook", key="save_direct_ans"):
                            add_to_notebook(
                                title=f"Q: {clean_q}",
                                text=ans_text + ("\n\nKey Points:\n" + "\n".join([f"- {p}" for p in key_pts]) if key_pts else ""),
                                source=f"{src_file} (p.{src_page})" if src_file else "",
                                category="Direct Answer",
                            )
                            st.toast("⭐ Direct Answer saved to Notebook!")

                st.markdown(f'<div class="sv-section-title">📖 {n} Ranked Source Extract{"s" if n != 1 else ""}</div>', unsafe_allow_html=True)
                for r in results:
                    score_pct = r.get("final_score_percent", 0.0)
                    sem_pct = r.get("semantic_score_percent")
                    kw_pct = r.get("keyword_score_percent")

                    score_details = ""
                    if sem_pct is not None:
                        score_details += f" · Semantic: {sem_pct:.1f}%"
                    if kw_pct is not None:
                        score_details += f" · Keyword: {kw_pct:.1f}%"

                    st.markdown(f"""
                    <div class="sv-result">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span class="rank">Result #{r['rank']}</span>
                            <span class="score">{score_color(score_pct)} {score_pct:.1f}% Match{score_details}</span>
                        </div>
                        <div class="text">{r['text']}</div>
                        <div class="cite">📁 {r['filename']} &nbsp;·&nbsp; 📄 Page {r['page_number']} &nbsp;·&nbsp; Chunk #{r['chunk_number']}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    btn_c1, btn_c2, btn_c3 = st.columns([2, 1, 1])
                    with btn_c1:
                        with st.expander(f"📋 Copy verbatim extract"):
                            st.text_area("Extract text", value=r["text"], height=100, key=f"copy_{r['chunk_id']}", label_visibility="collapsed")
                    with btn_c2:
                        render_tts_button(r["text"], label="🔊 Listen", button_id=f"tts_chk_{r['chunk_id']}")
                    with btn_c3:
                        if st.button("⭐ Bookmark", key=f"bm_{r['chunk_id']}"):
                            add_to_notebook(
                                title=f"Extract: {clean_q[:30]}",
                                text=r["text"],
                                source=f"{r['filename']} (p.{r['page_number']})",
                                category="Citation",
                            )
                            st.toast("⭐ Extract bookmarked to Notebook!")


# ═══════════════════════════════════════════════════════════════════
# PAGE: PRACTICE ARENA (3D Tactile Flip Cards & Anki Export)
# ═══════════════════════════════════════════════════════════════════
elif page == "🎯 Practice Arena":
    st.markdown("""
    <div class="sv-hero">
        <span class="pill pill-accent" style="margin-bottom:0.7rem;">🧠 Active Recall Testing</span>
        <h1>🎯 Practice Arena & 3D Flip Decks</h1>
        <p>Auto-generate high-yield question cards directly from your indexed materials. Click on the 3D card or press <b>Spacebar</b> to flip!</p>
    </div>
    """, unsafe_allow_html=True)

    docs = api_list_documents()
    indexed_docs = [d for d in docs if d.get("is_indexed")]

    # Card generation panel
    with st.expander("⚙️ Generate Question Cards & Anki Export", expanded=not st.session_state.quiz_cards):
        if not indexed_docs:
            st.warning("⚠️ No indexed documents available. Go to Library → Index a document first.")
        else:
            gen_cols = st.columns([3, 1, 1])
            gen_doc_names = {d["filename"]: d["id"] for d in indexed_docs}
            chosen_filenames = gen_cols[0].multiselect(
                "Select Source Documents",
                list(gen_doc_names.keys()),
                default=list(gen_doc_names.keys())[:2],
            )
            max_per = gen_cols[1].number_input("Max cards per doc", 1, 30, 8)
            if gen_cols[2].button("⚡ Generate Deck", type="primary", disabled=not chosen_filenames or not online):
                chosen_ids = [gen_doc_names[n] for n in chosen_filenames]
                with st.spinner("Extracting conceptual questions from documents…"):
                    result = api_generate_cards(chosen_ids, max_per_doc=int(max_per))
                if result:
                    st.session_state.quiz_cards = result.get("cards", [])
                    st.session_state.quiz_idx = 0
                    st.session_state.quiz_show_answer = False
                    st.session_state.quiz_score = 0
                    st.session_state.quiz_done = False
                    st.success(f"✅ Generated {result['total_generated']} practice cards!")
                    st.rerun()

    # ── Quiz interface with 3D Flip Card ──
    cards = st.session_state.quiz_cards
    if not cards:
        all_cards = api_list_flashcards()
        if all_cards:
            st.markdown("---")
            d1, d2 = st.columns([3, 2])
            d1.markdown(f"**{len(all_cards)} existing cards available in database** — Select documents above and click Generate to start a targeted quiz.")
            d2.download_button(
                label="📥 Export All Cards to Anki (.tsv)",
                data=generate_anki_tsv(all_cards),
                file_name="studyverse_anki_deck.tsv",
                mime="text/tab-separated-values",
                help="Download entire flashcard database formatted for direct import into Anki.",
            )

            with st.expander("📋 Browse existing question cards"):
                for c in all_cards[:20]:
                    with st.container():
                        q_col, a_col, del_col = st.columns([4, 4, 1])
                        q_col.markdown(f"**Q:** {c['question']}")
                        a_col.markdown(f"**A:** {c['answer'][:200]}")
                        if del_col.button("🗑️", key=f"del_card_{c['id']}", help="Delete card"):
                            api_delete_flashcard(c["id"])
                            st.rerun()
        else:
            st.info("🃏 No practice cards available yet. Ingest documents and click Generate Deck above.")
    else:
        idx = st.session_state.quiz_idx
        total = len(cards)

        st.download_button(
            label="📥 Export This Active Quiz to Anki (.tsv)",
            data=generate_anki_tsv(cards),
            file_name="studyverse_active_quiz.tsv",
            mime="text/tab-separated-values",
            help="Import this active quiz set directly into Anki desktop or mobile.",
        )

        if st.session_state.quiz_done or idx >= total:
            # Results screen
            score = st.session_state.quiz_score
            pct = round(score / total * 100) if total else 0
            st.markdown(f"""
            <div style="text-align:center; padding: 2.5rem; background: var(--sv-surface); border: 1px solid var(--sv-border); border-radius: 16px;">
                <div style="font-size:3.5rem;">{"🏆" if pct >= 70 else "📚"}</div>
                <h2 style="margin: 0.5rem 0;">Quiz Session Complete!</h2>
                <p style="font-size:1.6rem; font-weight:800; color: {'#10B981' if pct >= 70 else '#F59E0B'};">{score}/{total} Correct ({pct}%)</p>
                <p style="color: var(--sv-text-muted);">{"Superb mastery! Your retention is solid." if pct >= 70 else "Keep practising! Schedule regular reviews in the Revision Hub."}</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🔄 Restart Quiz Session", type="primary"):
                st.session_state.quiz_idx = 0
                st.session_state.quiz_show_answer = False
                st.session_state.quiz_score = 0
                st.session_state.quiz_done = False
                st.rerun()
        else:
            card = cards[idx]
            st.progress((idx) / total, text=f"Card {idx + 1} of {total} · {total - idx} remaining")

            # ── 3D Interactive Flip Card ──
            flipped_cls = "is-flipped" if st.session_state.quiz_show_answer else ""
            meta_str = f"📁 Document #{card.get('document_id', '?')} · Page {card.get('page_number', '?')}"

            st.markdown(f"""
            <div class="flip-card-container" onclick="this.querySelector('.flip-card').classList.toggle('is-flipped')">
                <div class="flip-card {flipped_cls}">
                    <div class="flip-card-front">
                        <div class="label">❓ Flashcard Question &nbsp;·&nbsp; <span style="font-weight:400; text-transform:none;">(Click or Space to Flip)</span></div>
                        <div class="qtext">{card['question']}</div>
                        <div class="flip-hint">👆 Click anywhere on card or press Spacebar to reveal answer</div>
                    </div>
                    <div class="flip-card-back">
                        <div class="label">✅ Verified Answer &nbsp;·&nbsp; <span style="font-weight:400; text-transform:none;">(Click or Space to Flip Back)</span></div>
                        <div class="atext">{card['answer']}</div>
                        <div class="flip-meta">{meta_str}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            render_tts_button(f"Question: {card['question']}. Answer: {card['answer']}", label="🔊 Read Question & Answer", button_id=f"tts_q_{idx}")

            if card.get("context"):
                with st.expander("📖 View source context chunk"):
                    st.caption(card["context"])

            # Interaction controls
            if not st.session_state.quiz_show_answer:
                if st.button("👁️ Reveal Answer", type="primary", use_container_width=True):
                    st.session_state.quiz_show_answer = True
                    st.rerun()
            else:
                st.markdown("**Did you recall correctly?**")
                c1, c2 = st.columns(2)
                if c1.button("✅ Correct Recall", type="primary", use_container_width=True):
                    st.session_state.quiz_score += 1
                    st.session_state.quiz_idx += 1
                    st.session_state.quiz_show_answer = False
                    if st.session_state.quiz_idx >= total:
                        st.session_state.quiz_done = True
                    st.rerun()
                if c2.button("❌ Needed Hint / Forgot", use_container_width=True):
                    st.session_state.quiz_idx += 1
                    st.session_state.quiz_show_answer = False
                    if st.session_state.quiz_idx >= total:
                        st.session_state.quiz_done = True
                    st.rerun()

        if st.button("⏭️ Finish Quiz"):
            st.session_state.quiz_done = True
            st.rerun()


# ═══════════════════════════════════════════════════════════════════
# PAGE: REVISION HUB (SuperMemo SM-2 Spaced Repetition Engine)
# ═══════════════════════════════════════════════════════════════════
elif page == "🔁 Revision Hub":
    st.markdown("""
    <div class="sv-hero">
        <span class="pill pill-accent" style="margin-bottom:0.7rem;">⏳ SuperMemo SM-2 Protocol</span>
        <h1>🔁 Revision Hub (Spaced Repetition)</h1>
        <p>Scientifically scheduled reviews using the SM-2 algorithm. Reinforce neural retention right before decay occurs.</p>
    </div>
    """, unsafe_allow_html=True)

    # Load due cards on page open
    if st.button("🔄 Refresh Due Cards Queue"):
        st.session_state.revision_queue = api_get_due_cards(limit=50)
        st.session_state.current_revision_idx = 0
        st.session_state.show_answer = False
        st.rerun()

    if not st.session_state.revision_queue:
        st.session_state.revision_queue = api_get_due_cards(limit=50)
        st.session_state.current_revision_idx = 0
        st.session_state.show_answer = False

    queue = st.session_state.revision_queue
    idx = st.session_state.current_revision_idx

    if not queue:
        st.balloons()
        st.success("🎉 **Outstanding! All revisions cleared for today.** No cards are currently due. Generate more practice cards in the Arena to expand your deck.")
    elif idx >= len(queue):
        score_display = f"{idx} cards reviewed in this session"
        st.markdown(f"""
        <div style="text-align:center; padding: 2.5rem; background: var(--sv-surface); border: 1px solid var(--sv-border); border-radius: 16px;">
            <div style="font-size:3rem;">🎊</div>
            <h2 style="margin: 0.5rem 0;">Session Complete!</h2>
            <p style="color: #10B981; font-weight: 700; font-size:1.2rem;">{score_display}</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🔄 Start New Review Session", type="primary"):
            st.session_state.revision_queue = api_get_due_cards(limit=50)
            st.session_state.current_revision_idx = 0
            st.session_state.show_answer = False
            st.rerun()
    else:
        card = queue[idx]
        remaining = len(queue) - idx

        st.progress(idx / len(queue), text=f"Progress: {idx}/{len(queue)} reviewed · {remaining} remaining today")

        meta_c1, meta_c2, meta_c3 = st.columns(3)
        meta_c1.metric("Repetitions", card.get("repetitions", 0))
        meta_c2.metric("Current Interval", f"{card.get('interval', 1)} day(s)")
        meta_c3.metric("Easiness Factor", f"{card.get('easiness_factor', 2.5):.2f}")

        # ── 3D Interactive Flip Card ──
        flipped_cls = "is-flipped" if st.session_state.show_answer else ""
        meta_str = f"Repetitions: {card.get('repetitions', 0)} · Interval: {card.get('interval', 1)}d · Ease: {card.get('easiness_factor', 2.5):.2f}"

        st.markdown(f"""
        <div class="flip-card-container" onclick="this.querySelector('.flip-card').classList.toggle('is-flipped')">
            <div class="flip-card {flipped_cls}">
                <div class="flip-card-front">
                    <div class="label">❓ Due Flashcard &nbsp;·&nbsp; <span style="font-weight:400; text-transform:none;">(Click or Space to Flip)</span></div>
                    <div class="qtext">{card['question']}</div>
                    <div class="flip-hint">👆 Click card or press Spacebar to inspect answer</div>
                </div>
                <div class="flip-card-back">
                    <div class="label">✅ Answer & Explanation &nbsp;·&nbsp; <span style="font-weight:400; text-transform:none;">(Click or Space to Flip Back)</span></div>
                    <div class="atext">{card['answer']}</div>
                    <div class="flip-meta">{meta_str}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        render_tts_button(card['answer'], label="🔊 Read Answer Aloud", button_id=f"tts_rev_{idx}")

        if card.get("context"):
            with st.expander("📖 View source context"):
                st.caption(card["context"])

        if not st.session_state.show_answer:
            if st.button("👁️ Reveal Answer & Rate Recall", type="primary", use_container_width=True):
                st.session_state.show_answer = True
                st.rerun()
        else:
            st.markdown("**Rate your recall speed and accuracy:**")
            grade_cols = st.columns(4)

            grade_map = [
                (0, "❌ Again",     "Forgot completely — reset interval", "secondary"),
                (3, "😓 Hard",      "Remembered with significant effort",  "secondary"),
                (4, "😊 Good",      "Correct after short hesitation",     "primary"),
                (5, "⚡ Easy",      "Instant effortless recall",           "primary"),
            ]

            for i, (quality, label, tooltip, btn_type) in enumerate(grade_map):
                with grade_cols[i]:
                    if st.button(label, key=f"grade_{quality}", help=tooltip, type=btn_type, use_container_width=True):
                        result = api_review_card(card["id"], quality)
                        if result:
                            next_days = result.get("interval", 1)
                            msg_map = {0: "Reset to 1d", 3: "Review in 1 day", 4: f"Scheduled in {next_days}d", 5: f"Scheduled in {next_days}d"}
                            st.toast(f"✅ Rated {label} — {msg_map.get(quality, '')}")
                        st.session_state.current_revision_idx += 1
                        st.session_state.show_answer = False
                        st.rerun()


# ═══════════════════════════════════════════════════════════════════
# PAGE: PROGRESS & ANALYTICS
# ═══════════════════════════════════════════════════════════════════
elif page == "📈 Progress":
    st.markdown("""
    <div class="sv-hero">
        <span class="pill pill-accent" style="margin-bottom:0.7rem;">📊 Retention Telemetry</span>
        <h1>📈 Progress & Study Streaks</h1>
        <p>Monitor your study momentum, memory consolidation curves, and mastery breakdown over time.</p>
    </div>
    """, unsafe_allow_html=True)

    if not online:
        st.warning("FastAPI backend is offline. Start the server via `start.bat` to retrieve progress.")
    else:
        prog = api_get_progress()
        if not prog:
            st.info("No study analytics recorded yet. Index documents and review cards to establish baseline data.")
        else:
            streak = prog.get("study_streak_days", 0)
            sc1, sc2, sc3 = st.columns([1, 3, 1])
            with sc2:
                st.markdown(f"""
                <div class="streak-badge">
                    🔥 {streak} Day{"s" if streak != 1 else ""} Streak
                    <small>Review cards daily to maintain memory consolidation!</small>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            m1, m2, m3, m4 = st.columns(4)
            metric_card(m1, prog.get("total_documents", 0), "Documents", pill="Ingested")
            metric_card(m2, prog.get("total_indexed_chunks", 0), "Indexed Chunks", pill="Embedded")
            metric_card(m3, prog.get("total_flashcards", 0), "Flashcards", pill="Created")
            metric_card(m4, prog.get("due_today", 0), "Due Today", pill="SM-2 Due")

            st.markdown("<br>", unsafe_allow_html=True)

            # ── Card mastery breakdown ──
            st.markdown('<div class="sv-section-title">📊 Flashcard Mastery Distribution</div>', unsafe_allow_html=True)
            total_cards = prog.get("total_flashcards", 0)
            mastered = prog.get("cards_mastered", 0)
            learning = prog.get("cards_learning", 0)
            new_cards = prog.get("cards_new", 0)

            if total_cards > 0:
                col_m, col_l, col_n = st.columns(3)
                with col_m:
                    metric_card(col_m, f"🏆 {mastered}", "Mastered (3+ reviews)", pill="Retained")
                with col_l:
                    metric_card(col_l, f"📖 {learning}", "Consolidating", pill="Learning")
                with col_n:
                    metric_card(col_n, f"🆕 {new_cards}", "New (Pending)", pill="Unreviewed")

                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("**Overall Mastery Percentage:**")
                if mastered > 0:
                    st.progress(mastered / total_cards, text=f"Mastered: {mastered}/{total_cards} ({mastered/total_cards*100:.0f}%)")
            else:
                st.info("No flashcards found. Generate questions in Practice Arena to populate mastery metrics.")

            # ── Retention rate ──
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="sv-section-title">🎯 Memory Retention Score</div>', unsafe_allow_html=True)
            r1, r2 = st.columns(2)
            retention = prog.get("retention_rate_percent", 100.0)
            total_reviews = prog.get("total_reviews_completed", 0)

            with r1:
                metric_card(r1, f"{retention:.0f}%", "Retention Rate", pill="SM-2 Accuracy")
            with r2:
                metric_card(r2, total_reviews, "Reviews Completed", pill="Drills Logged")

            if retention >= 90:
                st.success("🌟 Outstanding retention! Your cognitive consolidation is at peak efficiency.")
            elif retention >= 70:
                st.info("📚 Strong retention. Continue daily repetitions to graduate cards to long-term memory.")
            elif total_reviews > 0:
                st.warning("🔧 Retention dip detected. Revisit difficult passages in Search Notes.")


# ═══════════════════════════════════════════════════════════════════
# PAGE: NOTEBOOK & CITATIONS
# ═══════════════════════════════════════════════════════════════════
elif page == "📓 Notebook":
    st.markdown("""
    <div class="sv-hero">
        <span class="pill pill-accent" style="margin-bottom:0.7rem;">📝 Personal Study Repository</span>
        <h1>📓 Personal Notebook & Citations</h1>
        <p>Your saved citations, AI synthesis answers, and custom study notes. Fully exportable to Markdown for external review.</p>
    </div>
    """, unsafe_allow_html=True)

    nb_entries = st.session_state.notebook_entries

    col_btn1, col_btn2 = st.columns([1, 1])
    with col_btn2:
        if nb_entries:
            st.download_button(
                label="📥 Export Notebook to Markdown (.md)",
                data=export_notebook_markdown(),
                file_name="studyverse_notebook.md",
                mime="text/markdown",
                help="Download all your saved citations and notes into a clean Markdown document.",
            )

    # ── Create Note Form ──
    with st.expander("✍️ Create Custom Study Note", expanded=not nb_entries):
        with st.form("new_note_form", clear_on_submit=True):
            f_title = st.text_input("Note Title", placeholder="e.g. Core Principle of Paging vs Segmentation")
            f_cat = st.selectbox("Category", ["Concept Note", "Exam Tip", "Formula", "Question to Revise", "Summary"])
            f_content = st.text_area("Note Content (Markdown supported)", placeholder="Write your synthesis, explanation, or formulas here...", height=120)
            submitted = st.form_submit_button("💾 Save to Notebook", type="primary")
            if submitted:
                if f_title.strip() and f_content.strip():
                    add_to_notebook(title=f_title.strip(), text=f_content.strip(), category=f_cat)
                    st.success("✅ Note saved successfully!")
                    st.rerun()
                else:
                    st.error("Please supply both a title and note content.")

    # ── Display Entries ──
    st.markdown('<div class="sv-section-title">Saved Notes & Citations</div>', unsafe_allow_html=True)

    if not nb_entries:
        st.info("📝 No notebook entries yet. Bookmark extracts from Search Notes or create a custom note above.")
    else:
        categories = ["All"] + sorted(list({e.get("category", "Note") for e in nb_entries}))
        filter_cat = st.selectbox("Filter by Category", categories, index=0)

        filtered_entries = nb_entries if filter_cat == "All" else [e for e in nb_entries if e.get("category") == filter_cat]

        for e_idx, entry in enumerate(filtered_entries):
            with st.container():
                st.markdown(f"""
                <div class="notebook-card">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
                        <span style="font-weight:700; font-size:1.08rem; color: var(--sv-text-main);">{entry['title']}</span>
                        <span class="pill pill-blue">{entry.get('category', 'Note')}</span>
                    </div>
                    <div style="font-size:0.96rem; line-height:1.65; margin:0.6rem 0; color: var(--sv-text-main);">{entry['text']}</div>
                    <div style="font-size:0.8rem; color: var(--sv-text-muted); display:flex; justify-content:space-between; border-top:1px dashed var(--sv-border); padding-top:0.6rem; margin-top:0.6rem;">
                        <span>{f"📁 " + entry['source'] if entry.get('source') else ""}</span>
                        <span>🕒 {entry.get('date', '')}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                act_col1, act_col2 = st.columns([4, 1])
                with act_col1:
                    render_tts_button(entry["text"], label="🔊 Listen to Note", button_id=f"tts_nb_{entry['id']}")
                with act_col2:
                    if st.button("🗑️ Delete", key=f"del_nb_{entry['id']}"):
                        st.session_state.notebook_entries = [item for item in st.session_state.notebook_entries if item["id"] != entry["id"]]
                        st.rerun()
                st.divider()
