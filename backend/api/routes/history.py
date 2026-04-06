"""
api/routes/history.py — GET /api/v1/history — List past analyses
"""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.database import get_db
from backend.db import crud
from backend.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["History"])


@router.get("/history")
async def list_history(
    limit:  int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Return a paginated list of past analysis results."""
    analyses = await crud.list_analyses(db, limit=limit, offset=offset)
    return {
        "total":    len(analyses),
        "limit":    limit,
        "offset":   offset,
        "results":  [a.to_summary_dict() for a in analyses],
    }


@router.get("/history/{analysis_id}")
async def get_analysis(analysis_id: str, db: AsyncSession = Depends(get_db)):
    """Return full details of a specific past analysis."""
    analysis = await crud.get_analysis(db, analysis_id)
    if not analysis:
        raise HTTPException(404, f"Analysis '{analysis_id}' not found.")
    return {
        "id":               analysis.id,
        "resume_filename":  analysis.resume_filename,
        "jd_snippet":       analysis.jd_snippet,
        "ensemble_score":   analysis.ensemble_score,
        "tfidf_score":      analysis.tfidf_score,
        "sbert_score":      analysis.sbert_score,
        "bert_score":       analysis.bert_score,
        "ats_score":        analysis.ats_score,
        "skill_coverage":   analysis.skill_coverage,
        "skill_gap_data":   analysis.skill_gap_data,
        "section_scores":   analysis.section_scores,
        "suggestions":      analysis.suggestions,
        "ats_report":       analysis.ats_report,
        "missing_skills":   analysis.missing_skills,
        "created_at":       analysis.created_at.isoformat() if analysis.created_at else None,
    }
