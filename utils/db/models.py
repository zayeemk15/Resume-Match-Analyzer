"""
db/models.py — SQLAlchemy ORM models
"""
from __future__ import annotations
import datetime
import uuid
from sqlalchemy import Float, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from utils.db.database import Base


def _now() -> datetime.datetime:
    return datetime.datetime.utcnow()


def _uuid() -> str:
    return str(uuid.uuid4())


class ResumeFile(Base):
    __tablename__ = "resume_files"

    id: Mapped[str]           = mapped_column(String(36), primary_key=True, default=_uuid)
    filename: Mapped[str]     = mapped_column(String(255), nullable=False)
    file_size: Mapped[int]    = mapped_column(Integer, nullable=True)
    content_type: Mapped[str] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=_now)

    analyses: Mapped[list["AnalysisResult"]] = relationship(
        back_populates="resume", cascade="all, delete-orphan"
    )


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id: Mapped[str]             = mapped_column(String(36), primary_key=True, default=_uuid)
    resume_id: Mapped[str]      = mapped_column(String(36), ForeignKey("resume_files.id"), nullable=True)
    resume_filename: Mapped[str]= mapped_column(String(255), nullable=True)
    jd_snippet: Mapped[str]     = mapped_column(Text, nullable=True)  # first 300 chars of JD

    # Scores
    ensemble_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    tfidf_score:    Mapped[float] = mapped_column(Float, nullable=True)
    sbert_score:    Mapped[float] = mapped_column(Float, nullable=True)
    bert_score:     Mapped[float] = mapped_column(Float, nullable=True)
    ats_score:      Mapped[float] = mapped_column(Float, nullable=True)
    skill_coverage: Mapped[float] = mapped_column(Float, nullable=True)

    # Detailed results stored as JSON
    skill_gap_data:   Mapped[dict]  = mapped_column(JSON, nullable=True)
    section_scores:   Mapped[dict]  = mapped_column(JSON, nullable=True)
    suggestions:      Mapped[dict]  = mapped_column(JSON, nullable=True)
    ats_report:       Mapped[dict]  = mapped_column(JSON, nullable=True)
    missing_skills:   Mapped[list]  = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=_now)

    resume: Mapped["ResumeFile"] = relationship(back_populates="analyses")

    def to_summary_dict(self) -> dict:
        """Lightweight dict for history listing."""
        return {
            "id":             self.id,
            "resume_filename":self.resume_filename,
            "ensemble_score": self.ensemble_score,
            "ats_score":      self.ats_score,
            "skill_coverage": self.skill_coverage,
            "jd_snippet":     self.jd_snippet,
            "created_at":     self.created_at.isoformat() if self.created_at else None,
        }
