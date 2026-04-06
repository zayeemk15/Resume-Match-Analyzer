"""
app.py — Main Streamlit dashboard for the AI Resume Analyzer
Refactored for Production (Render)
"""
import sys
import asyncio
from pathlib import Path
import streamlit as st

# ── Page config (MUST be first Streamlit call) ──────────────────
st.set_page_config(
    page_title="Resume match analyzer by zayeem",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize Engine
from utils.engine import init_engine
from utils.db.database import get_db

@st.cache_resource
def startup_logic():
    asyncio.run(init_engine())

startup_logic()

# ── Custom CSS ──
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

.stApp {
    background-color: #F8FAFC !important;
    background-image: 
        radial-gradient(at 0% 0%, var(--bg-mesh-1) 0, transparent 50%), 
        radial-gradient(at 50% 0%, var(--bg-mesh-2) 0, transparent 50%), 
        radial-gradient(at 100% 0%, var(--bg-mesh-3) 0, transparent 50%) !important;
    background-attachment: fixed !important;
}

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
    font-size: 3.5rem !important;
    font-weight: 800 !important;
    background: linear-gradient(135deg, #0F172A 0%, var(--primary-alt) 100%);
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    margin-bottom: 0.75rem !important;
    line-height: 1.1 !important;
}
.main-header p { font-size: 1.2rem !important; color: var(--text-muted) !important; font-weight: 600 !important; }

[data-testid="stVerticalBlockBorderWrapper"] > div {
    background: var(--glass-bg) !important; 
    backdrop-filter: blur(16px) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 20px !important;
    padding: 1.5rem !important;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08) !important;
}

.stButton>button {
    background: linear-gradient(135deg, var(--primary), var(--secondary)) !important;
    border-radius: 12px !important;
    border: none !important;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ── Sidebar ──
with st.sidebar:
    st.markdown("### Navigation")
    page = st.radio(
        "Navigation",
        ["Analyzer", "Resume Ranker", "History", "About"],
        label_visibility="collapsed",
    )
    
    st.markdown("---")
    st.markdown("**System Status**")
    st.markdown('<div style="background: rgba(16, 185, 129, 0.15); border-radius: 8px; padding: 10px; text-align: center; border: 1px solid rgba(16, 185, 129, 0.3)"><span style="color:#065F46; font-weight:800;">● System Live</span></div>', unsafe_allow_html=True)
    
    st.markdown("---")
    st.caption("Release v2.1.0 Production")

# ── Pages ──
if page == "Analyzer":
    from utils.components.upload import render_upload
    asyncio.run(render_upload())

elif page == "Resume Ranker":
    from utils.components.ranker import render_ranker
    asyncio.run(render_ranker())

elif page == "History":
    from utils.components.history_view import render_history
    asyncio.run(render_history())

elif page == "About":
    st.markdown("""
<div class="about-card" style="background: white; border-radius: 16px; padding: 32px; box-shadow: 0 8px 30px rgba(0,0,0,0.08); margin-top: 20px; line-height: 1.6;">
    <h2 style="font-weight: bold; margin-bottom: 20px;">👤 About Me</h2>
    <p>I am an <strong>AI & Data Science Engineer</strong> passionate about building intelligent, real-world applications.</p>
    <p style="margin-top: 20px;">This project (<strong>Resume match analyzer by zayeem</strong>) is a production-ready ATS simulator using advanced NLP like TF-IDF and SBERT.</p>
    <div style="background: #F8FAFC; padding: 20px; border-radius: 12px; border: 1px solid #E2E8F0; margin-top: 24px;">
        <h3 style="font-size: 1.2rem; font-weight: 700; margin-bottom: 15px;">📩 Contact Me:</h3>
        <p><strong>LinkedIn:</strong> <a href="https://www.linkedin.com/in/zayeemkhateeb" target="_blank">zayeemkhateeb</a></p>
        <p><strong>Email:</strong> zayeem.s.khateeb@gmail.com</p>
    </div>
</div>""", unsafe_allow_html=True)
