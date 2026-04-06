"""
utils/engine.py — Main orchestration logic for the Resume Match Analyzer.
Consolidates the business logic previously handled by FastAPI routes.
"""
from __future__ import annotations
import uuid
import asyncio
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from utils.db import crud, models
from utils.db.database import get_db, create_tables
from utils.nlp.text_extractor import text_extractor
from utils.nlp.preprocessor import preprocessor
from utils.nlp.similarity_engine import similarity_engine
from utils.nlp.skill_gap_analyzer import skill_gap_analyzer
from utils.nlp.ats_simulator import ats_simulator
from utils.nlp.section_analyzer import section_analyzer
from utils.nlp.llm_suggestions import llm_suggestions
from utils.core.config import settings
from utils.core.logging_config import get_logger

logger = get_logger(__name__)

async def init_engine():
    """Initialize the database tables."""
    await create_tables()
    logger.info("Database tables initialized.")

async def analyze_resume(
    resume_content: bytes,
    resume_filename: str,
    jd_text: str,
    db: AsyncSession
) -> dict:
    """
    Analyze a single resume against a job description.
    Integrated version of the original FastAPI /analyze route.
    """
    # ── 1. Text extraction ─────────────────────────────────────────
    file_ext = Path(resume_filename or "resume.pdf").suffix.lower()
    source_type = file_ext.lstrip(".")
    
    try:
        resume_text = text_extractor.extract(resume_content, source_type=source_type)
    except Exception as exc:
        logger.error(f"Text extraction failed: {exc}")
        raise ValueError(f"Could not extract text from resume: {exc}")

    # JD may be raw text or a URL
    if jd_text.strip().startswith("http"):
        try:
            jd_raw = text_extractor.extract(jd_text, source_type="url")
        except Exception as exc:
            raise ValueError(f"Could not fetch JD from URL: {exc}")
    else:
        jd_raw = jd_text

    if len(resume_text) < 50:
        raise ValueError("Resume appears to be empty or unreadable.")
    if len(jd_raw) < 30:
        raise ValueError("Job description is too short.")

    # ── 2. Run NLP pipeline ─────────────────────────────────────
    clean_resume = preprocessor.clean(resume_text)
    clean_jd     = preprocessor.clean(jd_raw)

    similarity   = similarity_engine.compute(clean_resume, clean_jd)
    skill_gap    = skill_gap_analyzer.analyze(clean_resume, clean_jd)
    ats_report   = ats_simulator.score(resume_text, jd_raw)
    sections     = section_analyzer.analyze(resume_text, jd_raw)
    suggestions  = llm_suggestions.generate(
        resume_text=resume_text,
        jd_text=jd_raw,
        missing_skills=skill_gap.all_missing[:10],
        match_score=similarity["ensemble_score"],
    )

    # ── 3. Persist to DB ────────────────────────────────────────
    resume_db = await crud.create_resume_file(
        db,
        filename=resume_filename,
        file_size=len(resume_content),
        content_type="application/octet-stream",
    )
    
    analysis = await crud.create_analysis(
        db,
        resume_id       =resume_db.id,
        resume_filename =resume_filename,
        jd_snippet      =jd_raw[:300],
        ensemble_score  =similarity["ensemble_score"],
        tfidf_score     =similarity.get("tfidf_score"),
        sbert_score     =similarity.get("sbert_score"),
        bert_score      =similarity.get("bert_score"),
        ats_score       =ats_report.ats_score,
        skill_coverage  =skill_gap.coverage_score,
        skill_gap_data  ={
            "missing_by_category": skill_gap.missing_by_category,
            "all_missing":         skill_gap.all_missing,
            "all_jd_skills":       skill_gap.all_jd_skills,
            "coverage_score":      skill_gap.coverage_score,
            "priority_gaps":       skill_gap.priority_gaps,
        },
        section_scores  =sections.section_scores,
        suggestions     ={
            "bullets":        suggestions.resume_bullets,
            "keywords":       suggestions.keyword_suggestions,
            "summary":        suggestions.summary_rewrite,
            "advice":         suggestions.overall_advice,
            "used_llm":       suggestions.used_llm,
        },
        ats_report      ={
            "ats_score":              ats_report.ats_score,
            "keyword_match_score":    ats_report.keyword_match_score,
            "format_score":           ats_report.format_score,
            "keyword_density_score":  ats_report.keyword_density_score,
            "matched_keywords":       ats_report.matched_keywords[:30],
            "missing_keywords":       ats_report.missing_keywords[:20],
            "format_feedback":        ats_report.format_feedback,
            "improvement_tips":       ats_report.improvement_tips,
        },
        missing_skills  =skill_gap.all_missing,
    )

    return {
        "analysis_id":   analysis.id,
        "resume_file":   resume_filename,
        "match_scores":  similarity,
        "skill_gap": {
            "coverage_score":       skill_gap.coverage_score,
            "missing_by_category":  skill_gap.missing_by_category,
            "all_missing":          skill_gap.all_missing,
            "priority_gaps":        skill_gap.priority_gaps,
            "learning_resources":   skill_gap.learning_resources,
        },
        "ats": {
            "ats_score":            ats_report.ats_score,
            "keyword_match_score":  ats_report.keyword_match_score,
            "format_score":         ats_report.format_score,
            "matched_keywords":     ats_report.matched_keywords[:20],
            "missing_keywords":     ats_report.missing_keywords[:10],
            "improvement_tips":     ats_report.improvement_tips,
        },
        "sections": {
            "scores":           sections.section_scores,
            "feedback":         sections.section_feedback,
            "strongest":        sections.strongest_section,
            "weakest":          sections.weakest_section,
            "overall_score":    sections.overall_section_score,
        },
        "suggestions": {
            "bullets":  suggestions.resume_bullets,
            "keywords": suggestions.keyword_suggestions,
            "summary":  suggestions.summary_rewrite,
            "advice":   suggestions.overall_advice,
            "used_llm": suggestions.used_llm,
        },
    }

async def rank_resumes(
    resumes: list[tuple[str, bytes]],
    jd_text: str
) -> dict:
    """
    Rank multiple resumes against a job description.
    """
    results = []
    for filename, content in resumes:
        file_ext = Path(filename or "resume.pdf").suffix.lower()
        try:
            resume_text = text_extractor.extract(content, source_type=file_ext.lstrip("."))
        except Exception as exc:
            results.append({
                "filename": filename,
                "error":    f"Could not read file: {exc}",
                "rank":     None,
            })
            continue

        clean_resume = preprocessor.clean(resume_text)
        clean_jd     = preprocessor.clean(jd_text)

        sim   = similarity_engine.compute(clean_resume, clean_jd)
        gaps  = skill_gap_analyzer.analyze(clean_resume, clean_jd)

        results.append({
            "filename":       filename,
            "ensemble_score": sim["ensemble_score"],
            "tfidf_score":    sim["tfidf_score"],
            "sbert_score":    sim["sbert_score"],
            "confidence":     sim["confidence"],
            "skill_coverage": gaps.coverage_score,
            "missing_skills": gaps.all_missing[:8],
            "rank":           None,
        })

    # Sort
    valid = [r for r in results if r.get("ensemble_score") is not None]
    valid.sort(key=lambda x: x["ensemble_score"], reverse=True)
    for i, item in enumerate(valid, start=1):
        item["rank"] = i

    return {
        "ranked_resumes":  valid,
        "errors":          [r for r in results if r.get("ensemble_score") is None],
        "jd_snippet":      jd_text[:200],
        "total_submitted": len(resumes),
        "total_ranked":    len(valid),
    }

async def get_history(db: AsyncSession, limit: int = 20) -> list:
    """Retrieve recent analysis history."""
    try:
        stmt = select(models.Analysis).order_by(models.Analysis.created_at.desc()).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())
    except Exception as exc:
        logger.error(f"History retrieval failed: {exc}")
        return []

async def delete_history_item(db: AsyncSession, analysis_id: str) -> bool:
    """Delete an analysis from history."""
    try:
        stmt = delete(models.Analysis).where(models.Analysis.id == analysis_id)
        await db.execute(stmt)
        await db.commit()
        return True
    except Exception as exc:
        logger.error(f"Deletion failed: {exc}")
        return False
