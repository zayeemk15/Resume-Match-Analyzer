"""
streamlit_app/components/ranker.py — Resume Ranker page
"""
from __future__ import annotations
import streamlit as st
import requests
import plotly.express as px
import pandas as pd

BACKEND_URL = "http://localhost:8000"


from utils.engine import rank_resumes

async def render_ranker():
    st.markdown("""
    <div class="main-header">
        <h1>Resume Ranker</h1>
        <p>Compare multiple candidates against a target job profile</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.subheader("Batch Upload")
        resume_files = st.file_uploader(
            "Upload multiple resumes",
            type=["pdf", "docx", "txt"],
            accept_multiple_files=True,
            help="SaaS Engine supports batch PDF, DOCX, and TXT processing",
            label_visibility="collapsed"
        )
        if resume_files:
            st.markdown(f'<div style="color: var(--primary); font-weight:600; padding-top:10px;">Loaded: {len(resume_files)} resumes</div>', unsafe_allow_html=True)

    with col2:
        st.subheader("Job Criteria")
        jd_text = st.text_area(
            "Paste the job description",
            height=200,
            placeholder="Paste target job requirements here...",
            label_visibility="collapsed"
        )

    st.markdown("<br><br>", unsafe_allow_html=True)
    _, btn_col, _ = st.columns([1, 1, 1])
    with btn_col:
        rank_btn = st.button("Rank Candidates", type="primary", use_container_width=True)

    if rank_btn:
        if not resume_files or len(resume_files) < 2:
            st.error("Please upload at least 2 candidates for comparison.")
            return
        if not jd_text.strip():
            st.error("Please provide the job requirements.")
            return

        with st.spinner("Calculating matching leaderboard..."):
            try:
                resumes_data = [
                    (f.name, f.getvalue())
                    for f in resume_files
                ]
                result = await rank_resumes(resumes_data, jd_text)
                _render_ranking(result)
            except Exception as exc:
                st.error(f"Critical System Error: {exc}")


def _render_ranking(result: dict):
    ranked = result.get("ranked_resumes", [])
    if not ranked:
        st.warning("No resumes matched the minimum criteria for ranking.")
        return

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("Ranking Leaderboard")

    # Leaderboard Chart
    df = pd.DataFrame(ranked)
    fig = px.bar(df, x="ensemble_score", y="filename", orientation="h",
                 color="ensemble_score", color_continuous_scale=["#6366F1", "#06B6D4"],
                 text="ensemble_score")
    fig.update_traces(texttemplate="%{text:.0f}%", textposition="outside", marker_line_width=0)
    fig.update_layout(height=max(300, len(ranked) * 60), paper_bgcolor="rgba(0,0,0,0)",
                       plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#0F172A", family="Outfit"), showlegend=False,
                       xaxis=dict(title="Compatibility (%)", range=[0, 115]))
    st.plotly_chart(fig, use_container_width=True)

    # Detailed Rankings
    for r in ranked:
        st.markdown(f"**Rank #{r['rank']} – {r['filename']}**")
        st.progress(r['ensemble_score'] / 100)
        
        missing = r.get("missing_skills", [])
        if missing:
            with st.expander("Detected Skill Gaps"):
                chips = "".join([f'<span class="skill-chip chip-red">{s}</span>' for s in missing[:15]])
                st.markdown(chips, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

    # Errors
    for err in result.get("errors", []):
        st.error(f"Could not process `{err['filename']}`: {err.get('error', 'unknown')}")
