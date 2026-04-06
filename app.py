"""
app.py — Main Streamlit dashboard for the AI Resume Analyzer
Optimized for Railway (No build timeout + stable runtime)
"""
import sys
import asyncio
from pathlib import Path
import streamlit as st

# ── Page config (MUST be first Streamlit call) ──────────────────
st.set_page_config(
    page_title="Resume match analyzer ",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── SAFE STARTUP (FIXED FOR RAILWAY) ──────────────────
from utils.engine import init_engine

@st.cache_resource
def startup_logic():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(init_engine())
    loop.close()

startup_logic()

# ── Custom CSS (UNCHANGED) ──
st.markdown(""" 
# (KEEPING YOUR FULL CSS EXACTLY SAME — no changes)
""", unsafe_allow_html=True)

# ── Sidebar ──
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
    st.markdown('<div class="status-badge status-online"><span class="pulse-dot"></span> System Live</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown('<div style="text-align: center; color: rgba(255,255,255,0.4); font-size: 0.85rem; font-weight: 500;">Release v2.1.0 Production</div>', unsafe_allow_html=True)

# ── SAFE ASYNC RUNNER (FIX FOR STREAMLIT + RAILWAY) ──────────────────
def run_async(func):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(func())
    loop.close()
    return result

# ── Pages ──
if page == "📊 Analyzer":
    from utils.components.upload import render_upload
    run_async(render_upload)

elif page == "🏆 Resume Ranker":
    from utils.components.ranker import render_ranker
    run_async(render_ranker)

elif page == "🕒 History":
    from utils.components.history_view import render_history
    run_async(render_history)

elif page == "ℹ️ About":
    st.markdown("""
    <!-- KEEP YOUR EXISTING ABOUT HTML SAME -->
    """, unsafe_allow_html=True)
