"""
streamlit_app/app.py — Main Streamlit dashboard for the AI Resume Analyzer
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

# ── Page config (MUST be first Streamlit call) ──────────────────
st.set_page_config(
    page_title="Resume Match Analyzer",
    layout="wide",
    initial_sidebar_state="expanded",
)

import requests
import json

BACKEND_URL = "http://localhost:8000"

# ── Custom CSS (Ultra-Premium Mesh & Glass & High Contrast) ─────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Inter:wght@400;500;600&display=swap');

:root {
    --primary: #6366F1;
    --primary-alt: #4F46E5;
    --secondary: #06B6D4;
    --bg-mesh-1: rgba(99, 102, 241, 0.15);
    --bg-mesh-2: rgba(6, 182, 212, 0.15);
    --bg-mesh-3: rgba(236, 72, 153, 0.1);
    --text-main: #0F172A;
    --text-muted: #475569;
    --glass-bg: rgba(255, 255, 255, 0.95);
    --glass-border: rgba(203, 213, 225, 0.8);
}

/* Moving Mesh Gradient Background */
.stApp {
    background-color: #F8FAFC !important;
    background-image: 
        radial-gradient(at 0% 0%, var(--bg-mesh-1) 0, transparent 50%), 
        radial-gradient(at 50% 0%, var(--bg-mesh-2) 0, transparent 50%), 
        radial-gradient(at 100% 0%, var(--bg-mesh-3) 0, transparent 50%) !important;
    background-attachment: fixed !important;
}

/* Global Typography & Deep Contrast for OS Dark Mode Overrides */
*, p, span, label, div, li, ul { font-family: 'Inter', sans-serif; }
.stMarkdown p, .stMarkdown span, .stMarkdown li, label, .stText p {
    color: var(--text-main) !important;
}

h1, h2, h3, h4, h5 { 
    font-family: 'Outfit', sans-serif !important; 
    letter-spacing: -0.02em !important; 
    color: var(--text-main) !important; 
}

.main-header { padding: 3.5rem 0; text-align: center; }
.main-header h1 {
    font-size: 4rem !important;
    font-weight: 800 !important;
    background: linear-gradient(135deg, #0F172A 0%, var(--primary-alt) 100%);
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    margin-bottom: 0.75rem !important;
    line-height: 1.1 !important;
}
.main-header p { font-size: 1.4rem !important; color: var(--text-muted) !important; font-weight: 600 !important; }

/* Strong Solid Card Fallbacks for Windows Explorer / Old Edge */
[data-testid="stVerticalBlockBorderWrapper"] > div {
    background: var(--glass-bg) !important; 
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 20px !important;
    padding: 1.5rem !important;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08) !important;
    transition: all 0.3s cubic-bezier(0.23, 1, 0.32, 1) !important;
}
[data-testid="stVerticalBlockBorderWrapper"] > div:hover {
    transform: translateY(-4px) !important;
    box-shadow: 0 20px 40px rgba(99, 102, 241, 0.15) !important;
    border-color: rgba(99, 102, 241, 0.4) !important;
}

/* Sidebar High Opacity */
[data-testid="stSidebar"] {
    background-color: rgba(255, 255, 255, 0.95) !important;
    backdrop-filter: blur(25px) !important;
    border-right: 1px solid rgba(203, 213, 225, 0.8) !important;
}
[data-testid="stSidebar"] h3 { font-size: 1.3rem !important; margin-top: 1rem !important; color: var(--text-main) !important; }
div[role="radiogroup"] label {
    padding: 12px 16px !important;
    border-radius: 12px !important;
    margin-bottom: 6px !important;
    transition: 0.2s !important;
    background: #F8FAFC !important; /* Base solid color avoiding transparency bugs */
    border: 1px solid rgba(0,0,0,0.05) !important;
}
div[role="radiogroup"] label:hover { background: rgba(99, 102, 241, 0.08) !important; }
div[role="radiogroup"] label[data-checked="true"] {
    background: linear-gradient(90deg, rgba(99, 102, 241, 0.15), rgba(255,255,255,1)) !important;
    border-left: 5px solid var(--primary) !important;
}
div[role="radiogroup"] label[data-checked="true"] p { color: var(--primary-alt) !important; font-weight: 800 !important; }
div[role="radiogroup"] > label > div:first-child { display: none !important; }

/* Strongly colored buttons (and keep text white securely) */
.stButton>button {
    background: linear-gradient(135deg, var(--primary), var(--secondary)) !important;
    padding: 14px 32px !important;
    border-radius: 12px !important;
    border: none !important;
    box-shadow: 0 8px 20px rgba(99, 102, 241, 0.3) !important;
    transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
}
.stButton>button p, .stButton>button span {
    color: #FFFFFF !important;
    font-weight: 700 !important;
    font-size: 1.1rem !important;
}
.stButton>button:hover {
    transform: scale(1.03) translateY(-2px) !important;
    box-shadow: 0 12px 30px rgba(99, 102, 241, 0.4) !important;
}

/* Progress Bars */
.stProgress > div > div > div > div {
    background-image: linear-gradient(to right, var(--primary), var(--secondary)) !important;
    height: 14px !important;
    border-radius: 8px !important;
}

/* Tab Contrast */
[data-testid="stTabs"] { border-bottom: 2px solid rgba(203, 213, 225, 0.8) !important; }
[data-testid="stTabs"] button { font-size: 1.15rem !important; font-weight: 700 !important; padding: 12px 24px !important; color: var(--text-muted) !important; }
[data-testid="stTabs"] button[aria-selected="true"] { color: var(--primary-alt) !important; background: rgba(99, 102, 241, 0.08) !important; border-radius: 10px 10px 0 0 !important; }

/* Metric Solid Shadows */
[data-testid="stMetricValue"] { font-size: 2.8rem !important; font-weight: 800 !important; color: var(--primary-alt) !important; text-shadow: 0 2px 4px rgba(0,0,0,0.05); }
[data-testid="stMetricLabel"] { font-size: 1.1rem !important; color: var(--text-main) !important; font-weight: 700 !important; }

/* Text Inputs Legibility */
input, textarea {
    background: #FFFFFF !important;
    color: var(--text-main) !important;
    font-weight: 500 !important;
    border: 2px solid var(--glass-border) !important;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ── Sidebar ─────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Navigation")
    page = st.radio(
        "Navigation",
        ["Analyzer", "Resume Ranker", "History", "About"],
        label_visibility="collapsed",
    )
    
    st.markdown("---")
    st.markdown("**Core Status**")
    try:
        resp = requests.get(f"{BACKEND_URL}/health", timeout=2)
        if resp.ok:
            st.markdown('<div style="background: rgba(16, 185, 129, 0.15); border-radius: 8px; padding: 10px; text-align: center; border: 1px solid rgba(16, 185, 129, 0.3)"><span style="color:#065F46; font-weight:800;">● Online</span></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="background: rgba(245, 158, 11, 0.15); border-radius: 8px; padding: 10px; text-align: center; border: 1px solid rgba(245, 158, 11, 0.3)"><span style="color:#92400E; font-weight:800;">● Degraded</span></div>', unsafe_allow_html=True)
    except Exception:
        st.markdown('<div style="background: rgba(239, 68, 68, 0.15); border-radius: 8px; padding: 10px; text-align: center; border: 1px solid rgba(239, 68, 68, 0.3)"><span style="color:#991B1B; font-weight:800;">● Offline</span></div>', unsafe_allow_html=True)
    
    st.markdown("---")
    st.caption("Release v2.0.1 Ultimate")







# ── Pages ────────────────────────────────────────────────────────
if page == "Analyzer":
    from streamlit_app.components.upload import render_upload
    from streamlit_app.components.results import render_results
    render_upload()

elif page == "Resume Ranker":
    from streamlit_app.components.ranker import render_ranker
    render_ranker()

elif page == "History":
    from streamlit_app.components.history_view import render_history
    render_history()

elif page == "About":
    st.markdown("""
<style>
.about-card {
    background: white;
    border-radius: 16px;
    padding: 32px;
    box-shadow: 0 8px 30px rgba(0,0,0,0.08);
    margin-top: 20px;
    line-height: 1.6;
}
.about-card h2, .about-card h3 {
    color: #0F172A !important;
    margin-top: 0;
}
.about-card p, .about-card span, .about-card li {
    color: #334155 !important;
    font-size: 1.05rem;
}
.contact-block {
    background: #F8FAFC;
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #E2E8F0;
    margin-top: 24px;
}
.contact-block a {
    transition: all 0.2s ease;
    text-decoration: none;
}
.contact-block a:hover {
    text-decoration: underline;
    opacity: 0.8;
}
</style>

<div class="about-card">
    <h2 style="font-weight: bold; margin-bottom: 20px;">👤 About Me</h2>
    <p>I am an <strong>AI & Data Science Engineer</strong> and <strong>Web Developer</strong> passionate about building intelligent, real-world applications.</p>
    <p style="margin-top: 15px; font-weight: 600;">I specialize in:</p>
    <ul style="list-style-type: none; padding-left: 5px;">
        <li>• Machine Learning & NLP</li>
        <li>• Generative AI Systems</li>
        <li>• Full-Stack Web Development</li>
        <li>• Data Analytics & Visualization</li>
    </ul>
    <p style="margin-top: 20px;">This project (<strong>Resume Match Analyzer</strong>) simulates real-world Applicant Tracking Systems (ATS) using advanced NLP techniques like TF-IDF, Sentence Transformers, and BERT-based embeddings.</p>
    <p style="margin-top: 20px;"><strong>🛠 Tech Stack:</strong><br>
    Python, FastAPI, Streamlit, Scikit-learn, NLP, Transformers</p>
    <p style="margin-top: 20px; color: #4F46E5 !important; font-weight: 700;">🚀 Open to internships and full-time opportunities in AI, Data Science, and Web Development.</p>
    <div class="contact-block">
        <h3 style="font-size: 1.2rem; font-weight: 700; margin-bottom: 15px;">📩 Contact Me:</h3>
        <p style="margin-bottom: 10px;"><strong>LinkedIn:</strong><br>
        <a href="https://www.linkedin.com/in/zayeemkhateeb" target="_blank" style="color:#4F46E5; font-weight:600;">
        https://www.linkedin.com/in/zayeemkhateeb
        </a></p>
        <p style="margin-bottom: 0;"><strong>Email:</strong><br>
        <a href="mailto:zayeem.s.khateeb@gmail.com" style="color:#2563EB; font-weight:600;">
        zayeem.s.khateeb@gmail.com
        </a></p>
    </div>
</div>""", unsafe_allow_html=True)
