"""
api/routes/rank.py — POST /api/v1/rank — Rank multiple resumes vs one JD
"""
from __future__ import annotations
from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from pathlib import Path
from backend.nlp.text_extractor import text_extractor
from backend.nlp.preprocessor import preprocessor
from backend.nlp.similarity_engine import similarity_engine
from backend.nlp.skill_gap_analyzer import skill_gap_analyzer
from backend.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["Ranking"])


@router.post("/rank")
async def rank_resumes(
    resumes: list[UploadFile] = File(..., description="2–10 resume files"),
    jd_text: str              = Form(..., description="Job description text"),
):
    """
    Rank multiple resumes against a single job description.

    Returns:
        Ranked list (highest match first) with per-resume scores and skill coverage.
    """
    logger.info("Received ranking request", count=len(resumes), filenames=[f.filename for f in resumes])
    if not (2 <= len(resumes) <= 10):
        raise HTTPException(400, f"Submit between 2 and 10 resumes for ranking. Received: {len(resumes)}")

    results = []
    for resume_file in resumes:
        file_ext = Path(resume_file.filename or "resume.pdf").suffix.lower()
        try:
            content = await resume_file.read()
            resume_text = text_extractor.extract(content, source_type=file_ext.lstrip("."))
        except Exception as exc:
            logger.warning("Skipping unreadable file", filename=resume_file.filename, error=str(exc))
            results.append({
                "filename": resume_file.filename,
                "error":    f"Could not read file: {exc}",
                "rank":     None,
            })
            continue

        clean_resume = preprocessor.clean(resume_text)
        clean_jd     = preprocessor.clean(jd_text)

        sim   = similarity_engine.compute(clean_resume, clean_jd)
        gaps  = skill_gap_analyzer.analyze(clean_resume, clean_jd)

        results.append({
            "filename":       resume_file.filename,
            "ensemble_score": sim["ensemble_score"],
            "tfidf_score":    sim["tfidf_score"],
            "sbert_score":    sim["sbert_score"],
            "confidence":     sim["confidence"],
            "skill_coverage": gaps.coverage_score,
            "missing_skills": gaps.all_missing[:8],
            "rank":           None,  # assigned after sorting
        })

    # Sort by ensemble_score descending
    valid = [r for r in results if r.get("ensemble_score") is not None]
    valid.sort(key=lambda x: x["ensemble_score"], reverse=True)
    for i, item in enumerate(valid, start=1):
        item["rank"] = i

    errors = [r for r in results if r.get("ensemble_score") is None]

    logger.info("Ranking complete", total=len(resumes), ranked=len(valid))

    return {
        "ranked_resumes":  valid,
        "errors":          errors,
        "jd_snippet":      jd_text[:200],
        "total_submitted": len(resumes),
        "total_ranked":    len(valid),
    }
