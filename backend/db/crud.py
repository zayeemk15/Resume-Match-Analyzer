"""
db/crud.py — Async CRUD operations for the database
"""
from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from backend.db.models import ResumeFile, AnalysisResult
from backend.core.logging_config import get_logger

logger = get_logger(__name__)


# ── ResumeFile ─────────────────────────────────────────────────
async def create_resume_file(
    db: AsyncSession,
    filename: str,
    file_size: int | None = None,
    content_type: str | None = None,
) -> ResumeFile:
    obj = ResumeFile(filename=filename, file_size=file_size, content_type=content_type)
    db.add(obj)
    await db.flush()
    return obj


async def get_resume_file(db: AsyncSession, file_id: str) -> ResumeFile | None:
    result = await db.execute(select(ResumeFile).where(ResumeFile.id == file_id))
    return result.scalar_one_or_none()


# ── AnalysisResult ─────────────────────────────────────────────
async def create_analysis(
    db: AsyncSession,
    *,
    resume_id: str | None = None,
    resume_filename: str | None = None,
    jd_snippet: str | None = None,
    ensemble_score: float,
    tfidf_score: float | None = None,
    sbert_score: float | None = None,
    bert_score: float | None = None,
    ats_score: float | None = None,
    skill_coverage: float | None = None,
    skill_gap_data: dict | None = None,
    section_scores: dict | None = None,
    suggestions: dict | None = None,
    ats_report: dict | None = None,
    missing_skills: list | None = None,
) -> AnalysisResult:
    obj = AnalysisResult(
        resume_id=resume_id,
        resume_filename=resume_filename,
        jd_snippet=jd_snippet[:300] if jd_snippet else None,
        ensemble_score=ensemble_score,
        tfidf_score=tfidf_score,
        sbert_score=sbert_score,
        bert_score=bert_score,
        ats_score=ats_score,
        skill_coverage=skill_coverage,
        skill_gap_data=skill_gap_data,
        section_scores=section_scores,
        suggestions=suggestions,
        ats_report=ats_report,
        missing_skills=missing_skills,
    )
    db.add(obj)
    await db.flush()
    logger.info("Analysis saved", analysis_id=obj.id, score=ensemble_score)
    return obj


async def get_analysis(db: AsyncSession, analysis_id: str) -> AnalysisResult | None:
    result = await db.execute(
        select(AnalysisResult).where(AnalysisResult.id == analysis_id)
    )
    return result.scalar_one_or_none()


async def list_analyses(
    db: AsyncSession, limit: int = 50, offset: int = 0
) -> list[AnalysisResult]:
    result = await db.execute(
        select(AnalysisResult)
        .order_by(desc(AnalysisResult.created_at))
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())
