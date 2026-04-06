"""
streamlit_app/app.py — Main Streamlit dashboard for the AI Resume Analyzer
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

# ── Page config (MUST be first Streamlit call) ──────────────────
st.set_page_config(
    page_title="Resume match anaalyzer by zayeem",
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
    --primary: #4F46E5;
    --secondary: #6366F1;
    --accent: #22C55E;
    --bg-gradient-start: #0A0F1A;
    --bg-gradient-end: #111827;
    --text-main: #FFFFFF;
    --text-muted: #94A3B8;
    --glass-bg: rgba(17, 24, 39, 0.7);
    --glass-border: rgba(255, 255, 255, 0.08);
}

/* Background */
.stApp {
    background: linear-gradient(135deg, var(--bg-gradient-start) 0%, var(--bg-gradient-end) 100%) !important;
    background-attachment: fixed !important;
}

/* Global Typography */
*, p, span, label, div, li, ul { font-family: 'Inter', sans-serif; }
.stMarkdown p, .stMarkdown span, .stMarkdown li, label, .stText p {
    color: var(--text-main) !important;
}

h1, h2, h3, h4, h5 { 
    font-family: 'Outfit', sans-serif !important; 
    letter-spacing: -0.02em !important; 
    color: var(--text-main) !important; 
}

/* Main Header */
.main-header { padding: 3.5rem 0; text-align: center; }
.main-header h1 {
    font-size: 4.5rem !important;
    font-weight: 800 !important;
    background: linear-gradient(135deg, #60A5FA 0%, #A855F7 100%);
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    margin-bottom: 0.75rem !important;
    line-height: 1.1 !important;
}
.main-header p { 
    font-size: 1.5rem !important; 
    color: var(--text-muted) !important; 
    font-weight: 500 !important; 
}

/* Glassmorphism Cards */
[data-testid="stVerticalBlockBorderWrapper"] > div {
    background: var(--glass-bg) !important; 
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 16px !important;
    padding: 1.5rem !important;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
    transition: all 0.3s ease !important;
}
[data-testid="stVerticalBlockBorderWrapper"] > div:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 12px 40px rgba(79, 70, 229, 0.2) !important;
    border-color: rgba(99, 102, 241, 0.3) !important;
}

.upload-card {
    background: rgba(17, 24, 39, 0.7);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 2rem;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    transition: all 0.3s ease;
    height: 100%;
}
.upload-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 40px rgba(79, 70, 229, 0.2);
    border-color: rgba(99, 102, 241, 0.3);
}
.upload-card h3 {
    margin-top: 0 !important;
    margin-bottom: 1.5rem !important;
    font-size: 1.5rem !important;
    color: var(--text-main) !important;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    padding-bottom: 0.75rem;
}


/* Sidebar High Contrast & Gradient */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #172554 100%) !important;
    backdrop-filter: blur(20px) !important;
    border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
}
[data-testid="stSidebar"] h3 { 
    font-size: 1.5rem !important; 
    font-weight: 700 !important;
    margin-top: 1rem !important; 
    color: var(--text-main) !important; 
}

/* Sidebar Navigation Items */
div[role="radiogroup"] label {
    padding: 14px 18px !important;
    border-radius: 12px !important;
    margin-bottom: 8px !important;
    transition: all 0.3s ease !important;
    background: transparent !important;
    border: 1px solid transparent !important;
    color: var(--text-muted) !important;
}
div[role="radiogroup"] label p {
    font-size: 1.1rem !important;
    font-weight: 500 !important;
    color: var(--text-muted) !important;
    transition: all 0.3s ease !important;
}
div[role="radiogroup"] label:hover { 
    background: rgba(255, 255, 255, 0.05) !important; 
    border-color: rgba(255, 255, 255, 0.1) !important;
    transform: translateX(4px);
}
div[role="radiogroup"] label:hover p {
    color: var(--text-main) !important;
}
div[role="radiogroup"] label[data-checked="true"] {
    background: rgba(79, 70, 229, 0.15) !important;
    border: 1px solid rgba(79, 70, 229, 0.3) !important;
    border-left: 4px solid var(--primary) !important;
    box-shadow: 0 0 15px rgba(79, 70, 229, 0.2) !important;
}
div[role="radiogroup"] label[data-checked="true"] p { 
    color: var(--text-main) !important; 
    font-weight: 600 !important; 
    text-shadow: 0 0 8px rgba(255,255,255,0.3) !important;
}
div[role="radiogroup"] > label > div:first-child { display: none !important; }

/* Buttons */
.stButton>button {
    background: linear-gradient(135deg, var(--primary), var(--secondary)) !important;
    padding: 14px 32px !important;
    border-radius: 12px !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    box-shadow: 0 8px 20px rgba(79, 70, 229, 0.3) !important;
    transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
}
.stButton>button p, .stButton>button span {
    color: #FFFFFF !important;
    font-weight: 600 !important;
    font-size: 1.1rem !important;
}
.stButton>button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 12px 30px rgba(99, 102, 241, 0.5) !important;
    border-color: rgba(255,255,255,0.3) !important;
}

/* Text Inputs Legibility */
input, textarea {
    background: rgba(15, 23, 42, 0.6) !important;
    color: var(--text-main) !important;
    font-weight: 500 !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 10px !important;
    transition: all 0.3s ease !important;
}
input:focus, textarea:focus {
    border-color: var(--secondary) !important;
    box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2) !important;
}
textarea::placeholder, input::placeholder {
    color: rgba(255,255,255,0.3) !important;
}

/* System Status Glow Animation */
@keyframes pulseGlow {
    0% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.4); }
    70% { box-shadow: 0 0 0 10px rgba(34, 197, 94, 0); }
    100% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); }
}
.status-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 10px 18px;
    border-radius: 12px;
    font-weight: 600;
    font-size: 1.05rem;
    letter-spacing: 0.02em;
    width: 100%;
}
.status-online {
    background: linear-gradient(135deg, rgba(20, 83, 45, 0.5), rgba(6, 78, 59, 0.8));
    border: 1px solid rgba(34, 197, 94, 0.3);
    color: var(--accent);
    box-shadow: 0 4px 15px rgba(34, 197, 94, 0.15);
}
.pulse-dot {
    width: 10px;
    height: 10px;
    background-color: var(--accent);
    border-radius: 50%;
    animation: pulseGlow 2s infinite;
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
        ["📊 Analyzer", "🏆 Resume Ranker", "🕒 History", "ℹ️ About"],
        label_visibility="collapsed",
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
        <div style="background: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05); box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
            <div style="font-size: 0.9rem; color: #94A3B8; margin-bottom: 8px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">System Status</div>
    """, unsafe_allow_html=True)
    try:
        resp = requests.get(f"{BACKEND_URL}/health", timeout=2)
        if resp.ok:
            st.markdown('<div class="status-badge status-online"><span class="pulse-dot"></span> System Live</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="background: rgba(245, 158, 11, 0.15); border-radius: 12px; padding: 10px; text-align: center; border: 1px solid rgba(245, 158, 11, 0.3)"><span style="color:#F59E0B; font-weight:800;">● Degraded</span></div>', unsafe_allow_html=True)
    except Exception:
        st.markdown('<div style="background: rgba(239, 68, 68, 0.15); border-radius: 12px; padding: 10px; text-align: center; border: 1px solid rgba(239, 68, 68, 0.3)"><span style="color:#EF4444; font-weight:800;">● Offline</span></div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown('<div style="text-align: center; color: rgba(255,255,255,0.4); font-size: 0.85rem; font-weight: 500;">Release v2.1.0 Production</div>', unsafe_allow_html=True)







# ── Pages ────────────────────────────────────────────────────────
if page == "📊 Analyzer":
    from streamlit_app.components.upload import render_upload
    from streamlit_app.components.results import render_results
    render_upload()

elif page == "🏆 Resume Ranker":
    from streamlit_app.components.ranker import render_ranker
    render_ranker()

elif page == "🕒 History":
    from streamlit_app.components.history_view import render_history
    render_history()

elif page == "ℹ️ About":
    st.markdown("""
<style>
.about-card {
    background: var(--glass-bg);
    backdrop-filter: blur(12px);
    border: 1px solid var(--glass-border);
    border-radius: 16px;
    padding: 32px;
    box-shadow: 0 8px 30px rgba(0,0,0,0.3);
    margin-top: 20px;
    line-height: 1.6;
}
.about-card h2, .about-card h3 {
    color: var(--text-main) !important;
    margin-top: 0;
}
.about-card p, .about-card span, .about-card li {
    color: var(--text-muted) !important;
    font-size: 1.05rem;
}
.contact-block {
    background: rgba(255, 255, 255, 0.03);
    padding: 20px;
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.05);
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
    <p style="margin-top: 20px;">This project (<strong>Resume match anaalyzer by zayeem</strong>) simulates real-world Applicant Tracking Systems (ATS) using advanced NLP techniques like TF-IDF, Sentence Transformers, and BERT-based embeddings.</p>
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
