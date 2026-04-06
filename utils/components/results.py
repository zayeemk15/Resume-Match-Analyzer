"""
streamlit_app/components/results.py — Full analysis results dashboard with Glassmorphism
"""
from __future__ import annotations
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd


def _score_color(score: float) -> str:
    if score >= 75: return "#10b981"
    if score >= 50: return "#f59e0b"
    return "#ef4444"


def render_results(data: dict):
    """Render the full analysis results dashboard."""
    st.markdown("<br>", unsafe_allow_html=True)
    
    match    = data.get("match_scores", {})
    skill_g  = data.get("skill_gap", {})
    ats      = data.get("ats", {})
    sections = data.get("sections", {})
    tips     = data.get("suggestions", {})

    ensemble = match.get("ensemble_score", 0)
    ats_sc   = ats.get("ats_score", 0)
    coverage = skill_g.get("coverage_score", 0)

    # ── Workflow Indicator: Stage 2 ──────────────────────────────
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
        box-shadow: 0 0 15px rgba(34, 197, 94, 0.4);
    }
    .step-circle.completed {
        background: var(--accent); color: #064E3B;
    }
    .step-circle.active {
        background: linear-gradient(135deg, var(--primary), var(--secondary)); color: white;
        box-shadow: 0 0 15px rgba(79, 70, 229, 0.4);
    }
    .step-line {
        width: 60px; height: 3px; border-radius: 2px;
        background: linear-gradient(90deg, var(--accent) 0%, var(--primary) 100%);
    }
    .step-text { font-weight: 600; font-size: 1.05rem; }
    .step-text.completed { color: var(--accent); }
    .step-text.active { color: var(--text-main); }
    </style>
    <div class="stepper-container">
        <div class="stepper-wrapper">
            <div class="step-circle completed">✓</div>
            <span class="step-text completed">Upload</span>
            <div class="step-line"></div>
            <div class="step-circle active">2</div>
            <span class="step-text active">Analyze</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Custom Glassy Metrics ──────────────────────────────────
    c1, c2, c3 = st.columns(3)
    metrics = [
        ("Overall Match", ensemble, "var(--primary)"),
        ("ATS Score", ats_sc, "#06B6D4"),
        ("Skill Coverage", coverage, "#10B981")
    ]
    
    for col, (label, val, color) in zip([c1, c2, c3], metrics):
        with col:
            st.markdown(f"""
            <div style="background: rgba(255,255,255,0.4); border: 1px solid rgba(255,255,255,0.6); border-radius: 20px; padding: 20px; text-align: center;">
                <div style="font-size: 0.9rem; font-weight: 600; color: var(--text-muted); margin-bottom: 5px;">{label}</div>
                <div style="font-size: 2.5rem; font-weight: 800; color: {color};">{val:.0f}%</div>
                <div style="width: 100%; background: rgba(0,0,0,0.05); height: 8px; border-radius: 4px; margin-top: 10px;">
                    <div style="width: {val}%; background: {color}; height: 100%; border-radius: 4px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # ── Tabs for detailed results ────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs([
        "Skill Gap", "ATS Report", "Section Scores", "Recommendations"
    ])

    with tab1:
        _render_skill_gap(skill_g)

    with tab2:
        _render_ats(ats)

    with tab3:
        _render_sections(sections)

    with tab4:
        _render_suggestions(tips, ensemble)


def _render_skill_gap(skill_g: dict):
    missing_by_cat = skill_g.get("missing_by_category", {})
    priority = skill_g.get("priority_gaps", [])
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.subheader("Top Priority Gaps")
        if priority:
            for gap in priority[:10]:
                st.markdown(f"**{gap['skill']}** – {gap['priority'].capitalize()} priority")
        else:
            st.success("No critical skill gaps found.")
            
    with col2:
        st.subheader("Distribution")
        if missing_by_cat:
            df = pd.DataFrame([{"Category": k, "Missing": len(v)} for k, v in missing_by_cat.items()])
            fig = px.bar(df, x="Missing", y="Category", orientation="h", color="Missing", 
                         color_continuous_scale=["#6366F1", "#06B6D4"])
            fig.update_layout(height=250, margin=dict(l=0, r=0, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)", 
                              plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#0F172A", family="Outfit"))
            st.plotly_chart(fig, use_container_width=True)

    if missing_by_cat:
        st.markdown("### Missing Skills by Category")
        for cat, skills in missing_by_cat.items():
            with st.expander(f"{cat} ({len(skills)} missing)"):
                chips = "".join([f'<span class="skill-chip chip-red">{s}</span>' for s in skills])
                st.markdown(chips, unsafe_allow_html=True)


def _render_ats(ats: dict):
    st.subheader("ATS Compliance Report")
    
    matched = ats.get("matched_keywords", [])
    missing = ats.get("missing_keywords", [])
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Matched Keywords**")
        chips = "".join([f'<span class="skill-chip chip-green">{kw}</span>' for kw in matched[:20]])
        st.markdown(chips if matched else "None identified", unsafe_allow_html=True)
        
    with c2:
        st.markdown("**Missing Keywords**")
        chips = "".join([f'<span class="skill-chip chip-red">{kw}</span>' for kw in missing[:20]])
        st.markdown(chips if missing else "None missing", unsafe_allow_html=True)
    
    st.markdown("---")
    tips = ats.get("improvement_tips", [])
    if tips:
        st.markdown("**Optimization Feedback**")
        for tip in tips:
            st.info(tip)


def _render_sections(sections: dict):
    scores = sections.get("scores", {})
    feedback = sections.get("feedback", {})
    
    st.subheader("Section Quality Scores")
    
    if scores:
        labels = list(scores.keys())
        values = [scores[k] for k in labels]
        
        fig = go.Figure(data=[
            go.Bar(name='Score', x=labels, y=values, marker_color='#6366F1', marker_line_width=0)
        ])
        fig.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font=dict(color="#0F172A", family="Outfit"), margin=dict(t=20, b=20, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)
        
        for section, fb in feedback.items():
            st.markdown(f"**{section}**: {fb}")
    else:
        st.warning("Insufficient section data detected.")


def _render_suggestions(tips: dict, match_score: float):
    st.subheader("AI Coach Recommendations")
    
    advice = tips.get("advice", "")
    if advice:
        st.markdown(f"**Master Advice:** *{advice}*")
    
    st.markdown("---")
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("**Suggested Impact Bullets**")
        for bullet in tips.get("bullets", [])[:5]:
            st.markdown(f"→ {bullet}")
            
    with c2:
        st.markdown("**Executive Summary Draft**")
        summary = tips.get("summary", "")
        if summary:
            st.markdown(f"*{summary}*")
