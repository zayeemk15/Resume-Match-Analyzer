"""
streamlit_app/components/history_view.py — Analysis history page
"""
from __future__ import annotations
import streamlit as st
import requests
import pandas as pd

BACKEND_URL = "http://localhost:8000"


from utils.engine import get_history
from utils.db.database import get_db

async def render_history():
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
        async for db in get_db():
            results = await get_history(db, limit=limit)
            break
    except Exception as exc:
        st.error(f"History currently unavailable: {exc}")
        return

    if not results:
        st.info("No records found. Start by analyzing a resume!")
        return

    # Summary table
    df_data = []
    for r in results:
        df_data.append({
            "Resume":    getattr(r, "resume_filename", "N/A"),
            "Match":     f"{getattr(r, 'ensemble_score', 0):.1f}%",
            "ATS":       f"{getattr(r, 'ats_score', 0):.1f}%",
            "Date":      str(getattr(r, "created_at", ""))[:10],
            "ID":        str(getattr(r, "id", "")),
        })
    df = pd.DataFrame(df_data)

    st.markdown("### Recent Analyses")
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Detail viewer
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Detail Viewer")
    selected_id = st.selectbox("Select Record ID to view full report:", df["ID"].tolist())
    
    if selected_id:
        # Find the selected record in memory since we already fetched it
        d = next((r for r in results if str(r.id) == selected_id), None)
        
        if d:
            sc1, sc2, sc3 = st.columns(3)
            with sc1:
                st.markdown("**Match Score**")
                st.progress(getattr(d, 'ensemble_score', 0) / 100)
                st.markdown(f"**{getattr(d, 'ensemble_score', 0):.1f}%**")
            with sc2:
                st.markdown("**ATS Score**")
                st.progress(getattr(d, 'ats_score', 0) / 100)
                st.markdown(f"**{getattr(d, 'ats_score', 0):.1f}%**")
            with sc3:
                st.markdown("**Skill Coverage**")
                st.progress(getattr(d, 'skill_coverage', 0) / 100)
                st.markdown(f"**{getattr(d, 'skill_coverage', 0):.1f}%**")
            
            st.markdown("---")
            with st.expander("View Improvements"):
                suggestions = getattr(d, "suggestions", {})
                if isinstance(suggestions, dict):
                    for b in suggestions.get("bullets", []):
                        st.markdown(f"- {b}")
                else:
                    st.write("No suggestions found.")
        else:
            st.error("Could not fetch record details.")
