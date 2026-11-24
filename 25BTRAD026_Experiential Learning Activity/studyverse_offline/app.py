"""
app.py — StudyVerse Offline (Phase A + Phase B)
================================================
Fully standalone Streamlit application.
No HTTP calls. No FastAPI. No LLMs. No cloud dependencies.

Phase A: Reliable Local PDF Search Core
Phase B: Source Verification + Active Recall + Spaced Revision

Run with:
    streamlit run app.py
from inside the studyverse_offline/ directory.
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

# ── Make sure local modules are importable ───────────────────────────────────
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import streamlit.runtime
if not streamlit.runtime.exists():
    from streamlit.web import cli as stcli
    sys.argv = ["streamlit", "run", str(Path(__file__).resolve()), *sys.argv[1:]]
    sys.exit(stcli.main())

import sqlite3
import streamlit as st

import database as db
from database import (
    DB_PATH,
    clear_revision_topics,
    delete_document,
    delete_revision_topic,
    get_all_chunks_for_docs,
    get_document,
    get_document_chunk_count,
    get_page_text,
    get_page_texts,
    get_revision_topic,
    insert_quiz_attempt,
    list_documents,
    list_quiz_attempts,
    list_revision_topics,
    upsert_revision_topic,
)
from pdf_processor import process_and_store_pdf
from quiz_engine import generate_quiz_questions, grade_quiz
from revision_engine import calculate_next_review, save_topic_revision
from search_engine import (
    KEYWORD_WEIGHT,
    SEMANTIC_WEIGHT,
    build_index,
    faiss_index_exists,
    highlight_snippet,
    hybrid_search,
    keyword_only_search,
    load_model,
    related_pages,
    semantic_only_search,
)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG & STYLING
# ═══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="StudyVerse Offline",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background-color: #ffffff !important; color: #0f172a !important; }
[data-testid="stSidebar"] { background-color: #f8fafc !important; border-right: 1px solid #e2e8f0; }
[data-testid="stHeader"] { background: transparent !important; }
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
.stDeployButton { display: none; }
.block-container { padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1100px; }

/* Hero banner */
.sv-hero {
    background: linear-gradient(135deg, #0f2944 0%, #1e5799 60%, #0f2944 100%);
    border-radius: 14px; padding: 1.5rem 1.8rem; margin-bottom: 1.2rem; color: white;
}
.sv-hero h1 { font-size: 1.7rem; font-weight: 700; margin: 0; }
.sv-hero p  { font-size: 0.92rem; opacity: 0.85; margin: 0.3rem 0 0; }

/* Status pills */
.pill {
    display: inline-block; padding: 0.15rem 0.65rem;
    border-radius: 999px; font-size: 0.72rem; font-weight: 600;
}
.pill-green { background:#e6f9f0; color:#1a6b42; border:1px solid #a3d9b5; }
.pill-amber { background:#fff7e6; color:#8a5700; border:1px solid #f5cc80; }
.pill-red   { background:#fde8e8; color:#9b1c1c; border:1px solid #f5a5a5; }
.pill-blue  { background:#e8f0fe; color:#1a56db; border:1px solid #93b4f7; }
.pill-gray  { background:#f3f4f6; color:#555e6e; border:1px solid #d1d5db; }

/* Result cards */
.sv-result {
    background: white; border: 1px solid #e2e8f0; border-radius: 12px;
    padding: 1.1rem 1.4rem; margin-bottom: 0.9rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05); transition: box-shadow 0.2s;
}
.sv-result:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.10); }
.sv-result .rank  { font-size:0.68rem; font-weight:700; color:#64748b; text-transform:uppercase; letter-spacing:0.1em; }
.sv-result .badge { font-size:0.72rem; font-weight:600; padding:0.12rem 0.5rem; border-radius:6px;
                    background:#f0f7ff; color:#1a56db; border:1px solid #bfdbfe; }
.sv-result .score { font-size:0.85rem; font-weight:600; color:#2563eb; margin:0.3rem 0; }
.sv-result .text  { font-size:0.93rem; line-height:1.7; color:#1e293b; margin:0.5rem 0; white-space:pre-wrap; }
.sv-result .cite  { font-size:0.75rem; color:#64748b; }
.sv-result .llm-note {
    font-size:0.72rem; color:#64748b; font-style:italic;
    border-top:1px solid #f1f5f9; margin-top:0.6rem; padding-top:0.5rem;
}
.sv-result .snippet {
    background:#fefce8; border-left:3px solid #eab308; border-radius:4px;
    padding:0.4rem 0.7rem; font-size:0.85rem; font-style:italic; margin:0.4rem 0;
    color:#422006;
}

/* Callouts */
.sv-callout-info {
    background:#eff6ff; border-left:4px solid #3b82f6; border-radius:6px;
    padding:0.7rem 1rem; margin:0.6rem 0; font-size:0.88rem; color:#1e40af;
}
.sv-callout-trust {
    background:#f0fdf4; border-left:4px solid #22c55e; border-radius:6px;
    padding:0.7rem 1rem; margin:0.6rem 0; font-size:0.88rem; color:#14532d;
}

/* Metric card */
.sv-metric-box {
    background:white; border:1px solid #e2e8f0; border-radius:10px;
    padding:0.9rem; text-align:center; box-shadow:0 1px 3px rgba(0,0,0,0.05);
}
.sv-metric-val { font-size:1.6rem; font-weight:700; color:#1e293b; }
.sv-metric-lbl { font-size:0.75rem; color:#64748b; text-transform:uppercase; font-weight:600; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL INIT
# ═══════════════════════════════════════════════════════════════════════════════
@st.cache_resource
def _init() -> tuple[bool, sqlite3.Connection]:
    fts5_ok = db.init_db()
    conn = db.get_connection()
    return fts5_ok, conn


FTS5_AVAILABLE, _CONN = _init()


def _conn() -> sqlite3.Connection:
    try:
        _CONN.execute("SELECT 1")
        return _CONN
    except sqlite3.ProgrammingError:
        return db.get_connection()


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
def status_pill(extraction_status: str, is_indexed: bool) -> str:
    if is_indexed:
        return '<span class="pill pill-green">✅ Indexed</span>'
    mapping = {
        "completed": '<span class="pill pill-blue">📄 Extracted</span>',
        "warning":   '<span class="pill pill-amber">⚠️ Warning</span>',
        "failed":    '<span class="pill pill-red">❌ Failed</span>',
        "pending":   '<span class="pill pill-gray">⏳ Pending</span>',
    }
    return mapping.get(extraction_status, f'<span class="pill pill-gray">{extraction_status}</span>')


def score_dot(pct: float) -> str:
    if pct >= 70: return "🟢"
    if pct >= 40: return "🟡"
    return "🔴"


def match_type_label(r: dict, mode: str) -> str:
    if mode == "hybrid":
        has_sem = r.get("semantic_score") is not None
        has_kw  = r.get("keyword_score")  is not None
        if has_sem and has_kw:
            return "Hybrid Match"
        if has_sem:
            return "Semantic Match"
        return "Keyword Match"
    if mode == "semantic":
        return "Semantic Match"
    return "Keyword Match"


# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARD HEADER SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════
conn = _conn()
docs_list = list_documents(conn)
rev_list = list_revision_topics(conn)
today_str = date.today().isoformat()

due_count = sum(1 for r in rev_list if r["next_review_date"] <= today_str)
need_rev_count = sum(1 for r in rev_list if r["status"] == "need_revision")
recent_quizzes = list_quiz_attempts(conn, limit=1)
latest_quiz_str = f"{recent_quizzes[0]['score']}/{recent_quizzes[0]['total_questions']}" if recent_quizzes else "None"

st.markdown("""
<div class="sv-hero">
    <h1>🎓 StudyVerse Offline</h1>
    <p>Local-first academic study assistant — 100% private PDF search, source verification, active recall & spaced revision.</p>
</div>
""", unsafe_allow_html=True)

# Dashboard metrics row
mcol1, mcol2, mcol3, mcol4 = st.columns(4)
with mcol1:
    st.markdown(f"""
    <div class="sv-metric-box">
        <div class="sv-metric-val">{len(docs_list)}</div>
        <div class="sv-metric-lbl">Uploaded PDFs</div>
    </div>
    """, unsafe_allow_html=True)
with mcol2:
    st.markdown(f"""
    <div class="sv-metric-box">
        <div class="sv-metric-val">{due_count}</div>
        <div class="sv-metric-lbl">Topics Due Today</div>
    </div>
    """, unsafe_allow_html=True)
with mcol3:
    st.markdown(f"""
    <div class="sv-metric-box">
        <div class="sv-metric-val">{need_rev_count}</div>
        <div class="sv-metric-lbl">Need Revision</div>
    </div>
    """, unsafe_allow_html=True)
with mcol4:
    st.markdown(f"""
    <div class="sv-metric-box">
        <div class="sv-metric-val">{latest_quiz_str}</div>
        <div class="sv-metric-lbl">Latest Quiz Score</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# ═══════════════════════════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════════════════════════
tab_lib, tab_search, tab_quiz, tab_revision, tab_about = st.tabs([
    "📚 Library",
    "🔍 Search Notes",
    "🧠 Practice Quiz",
    "📅 Revision Tracker",
    "ℹ️ About / Debug",
])


# ───────────────────────────────────────────────────────────────────────────────
# TAB 1 — LIBRARY
# ───────────────────────────────────────────────────────────────────────────────
with tab_lib:
    st.markdown("### 📚 Document Library")

    with st.expander("➕ Upload Documents (PDF, Word, PowerPoint)", expanded=True):
        uploaded_files = st.file_uploader(
            "Drop PDF, Word, or PowerPoint files here",
            type=["pdf", "docx", "pptx", "doc", "ppt"],
            accept_multiple_files=True,
            help="Upload text-based PDF, Word (.docx, .doc), or PowerPoint (.pptx, .ppt) files.",
            key="lib_uploader",
        )

        col_up, col_idx_all = st.columns([1, 1])

        if col_up.button("📤 Upload & Extract", type="primary", disabled=not uploaded_files, key="btn_upload"):
            upload_results = []
            warnings_list: list[str] = []

            with st.spinner("Saving and extracting text…"):
                for uf in uploaded_files:
                    res = process_and_store_pdf(conn, uf, uf.name)
                    upload_results.append(res)
                    if res["extraction_status"] == "warning":
                        warnings_list.append(f"{res['filename']}: {res['extraction_message']}")

            ok    = sum(1 for r in upload_results if r["extraction_status"] == "completed")
            warns = sum(1 for r in upload_results if r["extraction_status"] == "warning")
            fails = sum(1 for r in upload_results if r["extraction_status"] == "failed")

            if ok:
                st.success(f"✅ Extracted text from {ok} document(s).")
            if warns:
                st.warning(
                    f"⚠️ {warns} file(s) have no searchable text.\n"
                    "No searchable text was found in these files."
                )
            if fails:
                st.error(f"❌ {fails} file(s) could not be read as valid documents.")

    st.markdown("---")
    st.markdown("### 📂 Managed Documents")
    all_docs = list_documents(conn)

    if not all_docs:
        st.info("No documents uploaded yet. Upload your academic PDFs above to get started.")
    else:
        model = load_model()
        for doc in all_docs:
            doc_id = doc["id"]
            chunk_cnt = get_document_chunk_count(conn, doc_id)
            is_idx = faiss_index_exists(doc_id) and chunk_cnt > 0

            with st.container():
                c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
                c1.markdown(f"**📄 {doc['filename']}**")
                c2.markdown(f"Pages: `{doc['page_count']}` (Extracted: `{doc['extracted_page_count']}`)")
                c3.markdown(f"Chunks: `{chunk_cnt}` | {status_pill(doc['extraction_status'], is_idx)}", unsafe_allow_html=True)

                if c4.button("⚡ Index Document", key=f"idx_{doc_id}", disabled=is_idx or doc["extracted_page_count"] == 0):
                    with st.spinner(f"Indexing '{doc['filename']}'…"):
                        build_index(conn, doc_id, FTS5_AVAILABLE, model)
                    st.success(f"Indexed '{doc['filename']}'.")
                    st.rerun()

                if c4.button("🗑️ Delete", key=f"del_{doc_id}"):
                    delete_document(conn, doc_id)
                    st.success(f"Deleted '{doc['filename']}'.")
                    st.rerun()
                st.divider()


# ───────────────────────────────────────────────────────────────────────────────
# TAB 2 — SEARCH NOTES
# ───────────────────────────────────────────────────────────────────────────────
with tab_search:
    st.markdown("### 🔍 Search Notes")

    # Search query state pre-fill handling
    default_q = st.session_state.get("search_query", "")

    col_q, col_btn = st.columns([4, 1])
    query = col_q.text_input(
        "Search query",
        value=default_q,
        placeholder="Enter keyword, formula, or concept (e.g. 'gradient descent', 'F=ma')...",
        label_visibility="collapsed",
        key="search_query_input",
    )
    search_clicked = col_btn.button("🔍 Search", type="primary", use_container_width=True)

    with st.expander("⚙️ Search Controls & Filters", expanded=False):
        c1, c2, c3 = st.columns(3)
        mode = c1.radio("Search Mode", ["hybrid", "semantic", "keyword"], format_func=lambda x: x.capitalize())
        top_k = c2.slider("Top K Results", 1, 5, 3)
        min_rel = c3.slider("Min Relevance Threshold", 0.0, 1.0, 0.0, 0.05)

        # Document Filter
        all_docs_search = list_documents(conn)
        doc_options = {d["id"]: d["filename"] for d in all_docs_search}
        selected_doc_ids = st.multiselect(
            "Filter by Document(s)",
            options=list(doc_options.keys()),
            format_func=lambda x: doc_options[x],
            default=list(doc_options.keys()),
        )

    if query and (search_clicked or default_q):
        st.session_state["search_query"] = query
        doc_filter = selected_doc_ids if selected_doc_ids else None
        model = load_model()

        with st.spinner("Searching notes..."):
            if mode == "hybrid":
                results = hybrid_search(conn, model, query, doc_filter, top_k, FTS5_AVAILABLE)
            elif mode == "semantic":
                results = semantic_only_search(model, doc_filter, query, top_k)
            else:
                results = keyword_only_search(conn, query, doc_filter, top_k, FTS5_AVAILABLE)

        filtered = [r for r in results if r["final_score"] >= min_rel]

        if not results:
            st.info("No matching chunks found. Try broadening your query terms.")
        elif not filtered:
            st.warning("All results were below the min relevance threshold. Try lowering the threshold.")
        else:
            st.markdown(f"#### Retrieved {len(filtered)} result(s)")

            for rank, r in enumerate(filtered, start=1):
                doc_info = get_document(conn, r["document_id"])
                page_cnt = doc_info["page_count"] if doc_info else 1
                rel_pages = related_pages(r["page_number"], page_cnt)

                final_pct = round(r["final_score"] * 100, 1)
                sem_pct = round(r["semantic_score"] * 100, 1) if r.get("semantic_score") is not None else None
                kw_pct = round(r["keyword_score"] * 100, 1) if r.get("keyword_score") is not None else None

                match_lbl = match_type_label(r, mode)
                score_parts = [f"Combined: {final_pct}%"]
                if sem_pct is not None: score_parts.append(f"Semantic: {sem_pct}%")
                if kw_pct is not None: score_parts.append(f"Keyword: {kw_pct}%")

                snippet = ""
                if mode in ("keyword", "hybrid") and r.get("keyword_score"):
                    snippet = highlight_snippet(r["text"], query)

                rel_str = " · ".join(f"p.{p}" + (" ◀" if p == r["page_number"] else "") for p in rel_pages)

                st.markdown(f"""
                <div class="sv-result">
                  <div class="rank">Result #{rank} &nbsp;·&nbsp; <span class="badge">{match_lbl}</span></div>
                  <div class="score">{score_dot(final_pct)} {"  ·  ".join(score_parts)}</div>
                  <div class="cite">📁 {r['filename']} &nbsp;·&nbsp; 📄 Page {r['page_number']} &nbsp;·&nbsp; Chunk {r['chunk_number']}</div>
                  {"<div class='snippet'>🔍 Snippet: " + snippet + "</div>" if snippet else ""}
                  <div class="text">{r['text']}</div>
                  <div class="cite">Related pages: {rel_str}</div>
                  <div class="llm-note">🔒 This result was retrieved directly from your uploaded PDF. It was not generated by an LLM.</div>
                </div>
                """, unsafe_allow_html=True)

                # Card Actions Row
                act_col1, act_col2, act_col3, act_col4 = st.columns([3, 2, 2, 2])

                if act_col1.button("🧠 Practice This Topic", key=f"prac_{r['chunk_id']}_{rank}", type="secondary"):
                    st.session_state["quiz_topic"] = query
                    st.session_state["quiz_chunks"] = [r]
                    st.session_state["quiz_doc_id"] = r["document_id"]
                    st.session_state["quiz_filename"] = r["filename"]
                    st.session_state["quiz_page_number"] = r["page_number"]
                    st.toast("Topic loaded! Switch to 🧠 Practice Quiz tab to take the quiz.", icon="🧠")

                if act_col2.button("✅ Understood", key=f"und_{r['chunk_id']}_{rank}"):
                    save_topic_revision(conn, query, r["document_id"], r["filename"], r["page_number"], "understood")
                    st.toast("Saved status: Understood (Review in 7 days)", icon="✅")

                if act_col3.button("🔁 Tomorrow", key=f"tom_{r['chunk_id']}_{rank}"):
                    save_topic_revision(conn, query, r["document_id"], r["filename"], r["page_number"], "review_tomorrow")
                    st.toast("Saved status: Review Tomorrow (Review in 1 day)", icon="🔁")

                if act_col4.button("⚠️ Need Rev", key=f"nrev_{r['chunk_id']}_{rank}"):
                    save_topic_revision(conn, query, r["document_id"], r["filename"], r["page_number"], "need_revision")
                    st.toast("Saved status: Need Revision (Review in 1 day)", icon="⚠️")

                # Enhanced Source Page Reader Expander
                btn_label = f"📖 Read Source Page — {r['filename']}, p.{r['page_number']}"
                with st.expander(btn_label):
                    p_state_key = f"page_nav_{r['chunk_id']}_{rank}"
                    if p_state_key not in st.session_state:
                        st.session_state[p_state_key] = r["page_number"]

                    curr_p = st.session_state[p_state_key]

                    # Navigation controls
                    n1, n2, n3 = st.columns([1, 2, 1])
                    if n1.button("⬅️ Previous Page", key=f"prev_{r['chunk_id']}_{rank}", disabled=(curr_p <= 1)):
                        st.session_state[p_state_key] = curr_p - 1
                        st.rerun()

                    n2.markdown(f"<div style='text-align:center; font-weight:600;'>📄 Page {curr_p} of {page_cnt}</div>", unsafe_allow_html=True)

                    if n3.button("➡️ Next Page", key=f"next_{r['chunk_id']}_{rank}", disabled=(curr_p >= page_cnt)):
                        st.session_state[p_state_key] = curr_p + 1
                        st.rerun()

                    # Guidance & Trust Callouts
                    st.markdown("""
                    <div class="sv-callout-info">💡 <strong>Learning Guidance:</strong> Read this page and nearby pages for the complete definition, formula, and examples.</div>
                    <div class="sv-callout-trust">🔒 <strong>Source Trust Note:</strong> This page content comes directly from your uploaded PDF.</div>
                    """, unsafe_allow_html=True)

                    full_text = get_page_text(conn, r["document_id"], curr_p)

                    if curr_p == r["page_number"]:
                        st.markdown(f"**Retrieved Chunk Highlight:**")
                        st.info(r["text"])

                    if full_text:
                        st.text_area(
                            "Complete Page Extracted Text",
                            value=full_text,
                            height=250,
                            key=f"page_txt_{r['chunk_id']}_{rank}_{curr_p}",
                        )
                    else:
                        st.info("No extracted text available for this page.")

                st.write("")


# ───────────────────────────────────────────────────────────────────────────────
# TAB 3 — PRACTICE QUIZ
# ───────────────────────────────────────────────────────────────────────────────
with tab_quiz:
    st.markdown("### 🧠 Rule-Based Practice Quiz")

    quiz_topic = st.session_state.get("quiz_topic")
    quiz_chunks = st.session_state.get("quiz_chunks", [])
    quiz_doc_id = st.session_state.get("quiz_doc_id")
    quiz_filename = st.session_state.get("quiz_filename", "Document.pdf")
    quiz_page = st.session_state.get("quiz_page_number", 1)

    if not quiz_topic or not quiz_chunks:
        st.warning(
            "⚠️ No active topic selected for quiz.\n\n"
            "Go to the **🔍 Search Notes** tab, run a search, and click **🧠 Practice This Topic** on any result card."
        )
    else:
        st.markdown(f"#### Topic: **{quiz_topic}**")
        st.caption(f"Source: 📁 `{quiz_filename}` &nbsp;·&nbsp; 📄 Page {quiz_page}")
        st.markdown("""
        <div class="sv-callout-trust">
        🔒 <strong>Active Recall Disclaimer:</strong> These are rule-based active-recall prompts created from retrieved PDF text. No LLM generated these questions.
        </div>
        """, unsafe_allow_html=True)

        questions = generate_quiz_questions(
            quiz_topic, quiz_chunks, quiz_doc_id, quiz_filename, quiz_page
        )

        with st.form(key="quiz_form"):
            student_answers = {}
            for q in questions:
                st.markdown(f"**Question {q['id']}:** {q['prompt']}")
                if q["type"] == "true_false":
                    student_answers[q["id"]] = st.radio(
                        "Your Answer:",
                        options=q["options"],
                        key=f"q_{q['id']}",
                        index=0,
                    )
                elif q["type"] == "manual_recall":
                    student_answers[q["id"]] = st.text_area(
                        "Your Response:",
                        key=f"q_{q['id']}",
                        placeholder="Type your explanation...",
                    )
                else:
                    student_answers[q["id"]] = st.text_input(
                        "Your Answer:",
                        key=f"q_{q['id']}",
                        placeholder="Type your answer here...",
                    )
                st.write("")

            submit_quiz = st.form_submit_button("Submit Quiz", type="primary", use_container_width=True)

        if submit_quiz:
            score, total_auto, results = grade_quiz(student_answers, questions)
            insert_quiz_attempt(
                conn,
                topic=quiz_topic,
                document_id=quiz_doc_id,
                source_filename=quiz_filename,
                page_number=quiz_page,
                score=score,
                total_questions=total_auto,
            )

            pct = round((score / total_auto * 100.0), 1) if total_auto > 0 else 0.0
            st.markdown(f"### Quiz Results: **{score} / {total_auto}** ({pct}%)")

            for res in results:
                qid = res["question_id"]
                if res["is_manual"]:
                    st.info(f"**Q{qid} (Manual Recall):** {res['prompt']}\n\n{res['explanation']}")
                elif res["is_correct"]:
                    st.success(f"**Q{qid} ✅ Correct:** {res['explanation']}")
                else:
                    st.error(f"**Q{qid} ❌ Incorrect:** {res['explanation']}")

            # Save / Auto-recommend Revision Date
            st.markdown("---")
            st.markdown("#### Spaced Revision Schedule")
            new_status, new_reps, new_interval, next_date_str = calculate_next_review(
                "auto", quiz_score=score, quiz_total=total_auto
            )
            save_topic_revision(
                conn,
                quiz_topic,
                quiz_doc_id,
                quiz_filename,
                quiz_page,
                new_status,
                quiz_score=score,
                quiz_total=total_auto,
            )
            st.success(
                f"✅ Saved to Revision Tracker based on score ({score}/{total_auto}): "
                f"Status **{new_status}** → Next Review in **{new_interval} day(s)** ({next_date_str})"
            )


# ───────────────────────────────────────────────────────────────────────────────
# TAB 4 — REVISION TRACKER
# ───────────────────────────────────────────────────────────────────────────────
with tab_revision:
    st.markdown("### 📅 Simplified SM-2-Inspired Revision Tracker")

    all_revs = list_revision_topics(conn)
    due_revs = [r for r in all_revs if r["next_review_date"] <= today_str]
    overdue_revs = sorted(due_revs, key=lambda x: x["next_review_date"])

    n_due = len(due_revs)
    n_overdue = sum(1 for r in due_revs if r["next_review_date"] < today_str)
    n_need = sum(1 for r in all_revs if r["status"] == "need_revision")
    n_und = sum(1 for r in all_revs if r["status"] == "understood")

    rcol1, rcol2, rcol3, rcol4, rcol5 = st.columns(5)
    rcol1.metric("Due Today", n_due)
    rcol2.metric("Overdue", n_overdue)
    rcol3.metric("Need Revision", n_need)
    rcol4.metric("Understood", n_und)
    rcol5.metric("Total Tracked", len(all_revs))

    st.markdown("---")
    st.markdown("### ⏰ Revise Today")

    if not due_revs:
        st.success("🎉 No topics due for revision today! Great job.")
    else:
        for topic_item in overdue_revs:
            t_id = topic_item["id"]
            t_name = topic_item["topic"]
            t_file = topic_item["source_filename"]
            t_page = topic_item["page_number"]
            t_status = topic_item["status"]
            t_date = topic_item["next_review_date"]
            t_score = f"{topic_item['latest_quiz_score']}/{topic_item['latest_quiz_total']}" if topic_item["latest_quiz_score"] is not None else "None"

            with st.container():
                c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
                c1.markdown(f"**{t_name}**\n\n📁 `{t_file}` p.{t_page}")
                c2.markdown(f"Status: `{t_status}`\n\nLatest Quiz: `{t_score}`")
                c3.markdown(f"Next Review: `{t_date}`")

                if c4.button("🔍 Search Topic", key=f"srch_rev_{t_id}"):
                    st.session_state["search_query"] = t_name
                    st.toast(f"Set search query to '{t_name}'. Switch to Search Notes tab!", icon="🔍")

    st.markdown("---")
    st.markdown("### 📋 All Tracked Topics")

    status_filter = st.radio(
        "Filter Status",
        options=["All", "need_revision", "review_tomorrow", "understood"],
        format_func=lambda x: x.replace("_", " ").capitalize(),
        horizontal=True,
    )

    filtered_revs = list_revision_topics(conn, status_filter=status_filter)

    if not filtered_revs:
        st.info("No tracked topics matching filter.")
    else:
        for tr in filtered_revs:
            tr_id = tr["id"]
            with st.container():
                rc1, rc2, rc3, rc4 = st.columns([3, 2, 2, 2])
                rc1.markdown(f"**{tr['topic']}** (📁 `{tr['source_filename']}`, p.{tr['page_number']})")
                rc2.markdown(f"Status: `{tr['status']}` | Reps: `{tr['repetitions']}`")
                rc3.markdown(f"Review Date: `{tr['next_review_date']}` ({tr['interval_days']}d interval)")

                if rc4.button("🗑️ Remove", key=f"rm_topic_{tr_id}"):
                    delete_revision_topic(conn, tr_id)
                    st.success(f"Removed '{tr['topic']}' from revision tracker.")
                    st.rerun()

    st.markdown("---")
    st.markdown("### 📜 Recent Quiz Attempts")
    q_attempts = list_quiz_attempts(conn, limit=5)

    if not q_attempts:
        st.info("No quiz attempts recorded yet.")
    else:
        for qa in q_attempts:
            st.write(
                f"- **{qa['topic']}** — Score: `{qa['score']}/{qa['total_questions']}` ({qa['score_percent']}%) "
                f"on `{qa['attempted_at'][:10]}` (📁 `{qa['source_filename']}`, p.{qa['page_number']})"
            )

    st.markdown("---")
    with st.expander("⚠️ Clear Progress (Reset Revision Tracker Only)"):
        st.warning("⚠️ This clears local revision records only. Uploaded PDFs, indexes, and quiz attempts will remain.")
        confirm_cb = st.checkbox("I understand this will clear local revision tracker entries.", key="cb_clear_rev")
        if st.button("🗑️ Clear Revision Data", type="primary", disabled=not confirm_cb):
            clear_revision_topics(conn)
            st.success("Cleared revision tracker records.")
            st.rerun()


# ───────────────────────────────────────────────────────────────────────────────
# TAB 5 — ABOUT / DEBUG
# ───────────────────────────────────────────────────────────────────────────────
with tab_about:
    st.markdown("### ℹ️ About StudyVerse Offline")
    st.markdown("""
```
PDF Upload & Extraction (PyMuPDF)
    ↓
SQLite Storage (Documents, Pages, Chunks)
    ↓
Hybrid Search Engine (FTS5 BM25 + FAISS Vector Search)
    ↓
Source Verification (Visual Chunk Reader + Page Navigation)
    ↓
Active Recall (Rule-Based 3-Question Generator)
    ↓
Spaced Revision (Simplified SM-2-Inspired Tracker)
```
""")

    st.info(
        "**No LLMs used.** StudyVerse Offline operates entirely locally without cloud APIs, "
        "OpenAI, Gemini, Claude, Ollama, or LangChain. All search results and quiz prompts "
        "are strictly grounded in original PDF text."
    )

    with st.expander("🐞 System Debug Info"):
        docs = list_documents(conn)
        revs = list_revision_topics(conn)
        quizzes = list_quiz_attempts(conn, limit=100)

        st.write(f"**Database path:** `{DB_PATH}`")
        st.write(f"**FTS5 keyword search:** {'✅ Active' if FTS5_AVAILABLE else '⚠️ Fallback'}")
        st.write(f"**Total Documents:** {len(docs)}")
        st.write(f"**Total Tracked Revision Topics:** {len(revs)}")
        st.write(f"**Total Historical Quiz Attempts:** {len(quizzes)}")
