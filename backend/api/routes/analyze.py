"""
api/routes/analyze.py — POST /api/v1/analyze — Core resume vs JD analysis
"""
from __future__ import annotations
from pathlib import Path
from fastapi import APIRouter, File, Form, UploadFile, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.database import get_db
from backend.db import crud
from backend.nlp.text_extractor import text_extractor
from backend.nlp.preprocessor import preprocessor
from backend.nlp.similarity_engine import similarity_engine
from backend.nlp.skill_gap_analyzer import skill_gap_analyzer
from backend.nlp.ats_simulator import ats_simulator
from backend.nlp.section_analyzer import section_analyzer
from backend.nlp.llm_suggestions import llm_suggestions
from backend.core.config import settings
from backend.core.logging_config import get_logger
import aiofiles
import uuid

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["Analysis"])


@router.post("/analyze")
async def analyze(
    resume_file: UploadFile = File(..., description="Resume PDF or DOCX"),
    jd_text:    str         = Form(..., description="Job description text or URL"),
    db: AsyncSession = Depends(get_db),
):
    """
    Analyze a resume against a job description.

    Returns:
    - Match score (TF-IDF + SBERT + BERT ensemble)
    - Skill gap report with priority missing skills
    - ATS compliance score and feedback
    - Section-wise similarity scores
    - Actionable improvement suggestions
    """
    # ── 1. Save uploaded file ───────────────────────────────────
    file_ext = Path(resume_file.filename or "resume.pdf").suffix.lower()
    if file_ext not in (".pdf", ".docx", ".doc", ".txt"):
        raise HTTPException(400, f"Unsupported file type: {file_ext}")

    file_id = str(uuid.uuid4())
    save_path = settings.upload_dir / f"{file_id}{file_ext}"
    content = await resume_file.read()

    async with aiofiles.open(save_path, "wb") as f:
        await f.write(content)

    logger.info(
        "File uploaded",
        filename=resume_file.filename,
        size=len(content),
        file_id=file_id,
    )

    # ── 2. Extract text ─────────────────────────────────────────
    try:
        source_type = file_ext.lstrip(".")
        resume_text = text_extractor.extract(content, source_type=source_type)
    except Exception as exc:
        raise HTTPException(422, f"Could not extract text from resume: {exc}")

    # JD may be raw text or a URL
    if jd_text.strip().startswith("http"):
        try:
            jd_raw = text_extractor.extract(jd_text, source_type="url")
        except Exception as exc:
            raise HTTPException(422, f"Could not fetch JD from URL: {exc}")
    else:
        jd_raw = jd_text

    if len(resume_text) < 50:
        raise HTTPException(422, "Resume appears to be empty or unreadable.")
    if len(jd_raw) < 30:
        raise HTTPException(422, "Job description is too short.")

    # ── 3. Run NLP pipeline ─────────────────────────────────────
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

    # ── 4. Persist to DB ────────────────────────────────────────
    resume_db = await crud.create_resume_file(
        db,
        filename=resume_file.filename or "resume",
        file_size=len(content),
        content_type=resume_file.content_type,
    )
    analysis = await crud.create_analysis(
        db,
        resume_id       =resume_db.id,
        resume_filename =resume_file.filename,
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

    # ── 5. Build response ───────────────────────────────────────
    return {
        "analysis_id":   analysis.id,
        "resume_file":   resume_file.filename,
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
