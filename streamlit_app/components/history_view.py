"""
streamlit_app/components/history_view.py — Analysis history page
"""
from __future__ import annotations
import streamlit as st
import requests
import pandas as pd

BACKEND_URL = "http://localhost:8000"


def render_history():
    st.markdown("""
    <div class="main-header">
        <h1>Analysis History</h1>
        <p>Review and compare past resume matches</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns([1, 3])
    with c1:
        limit = st.selectbox("Records", [10, 25, 50, 100], index=0)

    try:
        resp = requests.get(f"{BACKEND_URL}/api/v1/history?limit={limit}", timeout=10)
        if not resp.ok:
            st.error("History currently unavailable.")
            return
        data = resp.json()
    except Exception:
        st.error("Backend connection failed.")
        return

    results = data.get("results", [])
    if not results:
        st.info("No records found. Start by analyzing a resume!")
        return

    # Summary table
    df = pd.DataFrame([{
        "Resume":    r.get("resume_filename", "N/A"),
        "Match":     f"{r.get('ensemble_score', 0):.1f}%",
        "ATS":       f"{r.get('ats_score', 0):.1f}%",
        "Date":      r.get("created_at", "")[:10],
        "ID":        r.get("id", ""),
    } for r in results])

    st.markdown("### Recent Analyses")
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Detail viewer
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="stCard">', unsafe_allow_html=True)
    st.markdown("### Detail Viewer")
    selected_id = st.selectbox("Select Record ID to view full report:", df["ID"].tolist())
    
    if selected_id:
        detail_resp = requests.get(f"{BACKEND_URL}/api/v1/history/{selected_id}", timeout=10)
        if detail_resp.ok:
            d = detail_resp.json()
            
            sc1, sc2, sc3 = st.columns(3)
            with sc1:
                st.markdown("**Match Score**")
                st.progress(d.get('ensemble_score', 0) / 100)
                st.markdown(f"**{d.get('ensemble_score', 0):.1f}%**")
            with sc2:
                st.markdown("**ATS Score**")
                st.progress(d.get('ats_score', 0) / 100)
                st.markdown(f"**{d.get('ats_score', 0):.1f}%**")
            with sc3:
                st.markdown("**Skill Coverage**")
                st.progress(d.get('skill_coverage', 0) / 100)
                st.markdown(f"**{d.get('skill_coverage', 0):.1f}%**")
            
            st.markdown("---")
            with st.expander("View Improvements"):
                suggestions = d.get("suggestions", {})
                for b in suggestions.get("bullets", []):
                    st.markdown(f"- {b}")
        else:
            st.error("Could not fetch record details.")
    st.markdown('</div>', unsafe_allow_html=True)
