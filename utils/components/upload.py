"""
streamlit_app/components/upload.py — Main Analyzer page: upload + analyze
"""
from __future__ import annotations
import streamlit as st
import requests
import json

BACKEND_URL = "http://localhost:8000"


from utils.engine import analyze_resume
from utils.db.database import get_db

async def render_upload():
    st.markdown("""
    <div class="main-header">
        <h1>Resume Match Analyzer</h1>
        <p>Advanced AI Candidate Evaluation & Skill Gap Scoring</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Workflow Indicator ──────────────────────────────────────
    st.markdown("""
    <div style="display: flex; justify-content: center; margin-bottom: 3rem;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="background: var(--primary); color: white; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700;">1</div>
            <span style="font-weight: 600; color: var(--text-main);">Upload</span>
            <div style="width: 50px; height: 2px; background: rgba(0,0,0,0.1);"></div>
            <div style="background: rgba(0,0,0,0.05); color: var(--text-muted); width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700;">2</div>
            <span style="font-weight: 600; color: var(--text-muted);">Analyze</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.subheader("Candidate Resume")
        resume_file = st.file_uploader(
            "Drop your resume here",
            type=["pdf", "docx", "txt"],
            help="SaaS Engine supports PDF, DOCX, and TXT formats",
            label_visibility="collapsed"
        )
        if resume_file:
            st.markdown(f'<div style="color: var(--primary); font-weight:600; padding-top:10px;">Ready: {resume_file.name}</div>', unsafe_allow_html=True)

    with col2:
        st.subheader("Target Job")
        jd_input_type = st.radio(
            "Method",
            ["Paste text", "URL"],
            horizontal=True,
            label_visibility="collapsed",
        )
        if jd_input_type == "Paste text":
            jd_text = st.text_area(
                "Paste requirements here",
                height=200,
                placeholder="Paste the Job Description or key requirements here...",
                label_visibility="collapsed"
            )
        else:
            jd_url = st.text_input("Job URL", placeholder="https://linkedin.com/jobs/...", label_visibility="collapsed")
            jd_text = jd_url if jd_url else ""

    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Analyze Button - Centered and Large
    _, btn_col, _ = st.columns([1, 1, 1])
    with btn_col:
        analyze_btn = st.button("Analyze Match", type="primary", use_container_width=True)

    if analyze_btn:
        if not resume_file:
            st.error("Please upload a resume.")
            return
        if not jd_text.strip():
            st.error("Please provide a job description.")
            return

        with st.spinner("Analyzing resume content..."):
            try:
                # Direct call to engine logic
                async for db in get_db():
                    data = await analyze_resume(
                        resume_content=resume_file.getvalue(),
                        resume_filename=resume_file.name,
                        jd_text=jd_text,
                        db=db
                    )
                    st.session_state["analysis"] = data
                    st.toast("Analysis ready")
                    break # Single session
            except Exception as exc:
                st.error(f"Analysis failed: {exc}")
                return

    if "analysis" in st.session_state:
        from utils.components.results import render_results
        render_results(st.session_state["analysis"])
