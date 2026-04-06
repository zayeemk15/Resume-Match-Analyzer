"""
streamlit_app/components/upload.py — Main Analyzer page: upload + analyze
"""
from __future__ import annotations
import streamlit as st
import requests
import json

BACKEND_URL = "http://localhost:8000"


def render_upload():
    st.markdown("""
    <div class="main-header">
        <h1>Resume Match Analyzer</h1>
        <p>Advanced AI Candidate Evaluation & Skill Gap Scoring</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Workflow Indicator: Stage 1 ──────────────────────────────
    st.markdown("""
    <style>
    .stepper-container {
        display: flex; justify-content: center; margin-bottom: 3rem; margin-top: 1rem;
    }
    .stepper-wrapper {
        display: flex; align-items: center; gap: 15px;
        background: var(--glass-bg); padding: 15px 30px; border-radius: 50px;
        border: 1px solid var(--glass-border); box-shadow: 0 4px 20px rgba(0,0,0,0.2);
        backdrop-filter: blur(12px);
    }
    .step-circle {
        width: 36px; height: 36px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center; font-weight: 700;
        box-shadow: 0 0 15px rgba(79, 70, 229, 0.4);
    }
    .step-circle.active {
        background: linear-gradient(135deg, var(--primary), var(--secondary)); color: white;
    }
    .step-circle.inactive {
        background: rgba(255,255,255,0.05); color: var(--text-muted); border: 1px solid rgba(255,255,255,0.1);
        box-shadow: none;
    }
    .step-line {
        width: 60px; height: 3px; border-radius: 2px;
        background: linear-gradient(90deg, var(--primary) 0%, rgba(255,255,255,0.1) 100%);
    }
    .step-text { font-weight: 600; font-size: 1.05rem; }
    .step-text.active { color: var(--text-main); }
    .step-text.inactive { color: var(--text-muted); }
    </style>
    <div class="stepper-container">
        <div class="stepper-wrapper">
            <div class="step-circle active">1</div>
            <span class="step-text active">Upload</span>
            <div class="step-line"></div>
            <div class="step-circle inactive">2</div>
            <span class="step-text inactive">Analyze</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        with st.container():
            st.markdown('<div class="upload-card">', unsafe_allow_html=True)
            st.markdown('<h3>📄 Candidate Resume</h3>', unsafe_allow_html=True)
            resume_file = st.file_uploader(
                "Drop your resume here",
                type=["pdf", "docx", "txt"],
                help="SaaS Engine supports PDF, DOCX, and TXT formats",
                label_visibility="collapsed"
            )
            if resume_file:
                st.markdown(f'<div style="color: var(--accent); font-weight:600; padding-top:10px; text-shadow: 0 0 8px rgba(34,197,94,0.3);">✨ Ready: {resume_file.name}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        with st.container():
            st.markdown('<div class="upload-card">', unsafe_allow_html=True)
            st.markdown('<h3>🎯 Target Job / Role</h3>', unsafe_allow_html=True)
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
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Analyze Button - Centered and Large
    _, btn_col, _ = st.columns([1, 1, 1])
    with btn_col:
        analyze_btn = st.button("🚀 Analyze Match", type="primary", use_container_width=True)

    if analyze_btn:
        if not resume_file:
            st.error("Please upload a resume.")
            return
        if not jd_text.strip():
            st.error("Please provide a job description.")
            return

        with st.spinner("Analyzing resume content..."):
            try:
                response = requests.post(
                    f"{BACKEND_URL}/api/v1/analyze",
                    files={"resume_file": (resume_file.name, resume_file.getvalue(), resume_file.type)},
                    data={"jd_text": jd_text},
                    timeout=120,
                )
                # ── Tabs for detailed results ────────────────────────────────
                tab1, tab2, tab3, tab4 = st.tabs([
                    "Skill Gap", "ATS Report", "Section Scores", "Recommendations"
                ])
                if response.ok:
                    data = response.json()
                    st.session_state["analysis"] = data
                    st.toast("Analysis ready")
                else:
                    st.error(f"API Error {response.status_code}: {response.json().get('detail', 'Unknown error')}")
                    return
            except requests.exceptions.ConnectionError:
                st.error("Backend connection failed")
                return
            except Exception as exc:
                st.error(f"Error: {exc}")
                return

    if "analysis" in st.session_state:
        from streamlit_app.components.results import render_results
        render_results(st.session_state["analysis"])
