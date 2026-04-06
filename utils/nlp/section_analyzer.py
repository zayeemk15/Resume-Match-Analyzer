"""
nlp/section_analyzer.py — Section-by-section resume vs JD comparison
"""
from __future__ import annotations
from dataclasses import dataclass, field
from utils.nlp.preprocessor import preprocessor
from utils.nlp.similarity_engine import similarity_engine
from utils.core.logging_config import get_logger

logger = get_logger(__name__)

# Map resume sections → relevant JD keywords to compare against
SECTION_JD_KEYWORDS = {
    "experience":    ["experience", "responsibilities", "duties", "works", "manage"],
    "education":     ["education", "degree", "university", "bachelor", "master", "phd", "gpa"],
    "skills":        ["skills", "technologies", "proficient", "expertise", "tools"],
    "projects":      ["projects", "portfolio", "built", "developed", "side projects"],
    "certifications":["certifications", "licenses", "certified", "credentials"],
    "summary":       ["objective", "profile", "about", "summary"],
    "achievements":  ["achievements", "awards", "recognition", "honors"],
}


@dataclass
class SectionAnalysis:
    section_scores: dict[str, float]         # section → similarity score (0–100)
    section_feedback: dict[str, str]         # section → feedback string
    strongest_section: str
    weakest_section: str
    overall_section_score: float


class SectionAnalyzer:
    """
    Analyzes each section of a resume independently against the JD.
    Provides granular feedback per section.
    """

    def analyze(self, resume_text: str, jd_text: str) -> SectionAnalysis:
        """
        Break resume into sections and score each against the full JD.
        Falls back to whole-document score if section not detected.
        """
        parsed = preprocessor.process(resume_text)
        sections = parsed.sections

        scores: dict[str, float] = {}
        feedback: dict[str, str] = {}

        for section_name, section_content in sections.items():
            if not section_content.strip() or section_name == "other":
                continue
            try:
                result = similarity_engine.compute(section_content, jd_text)
                score = result["sbert_score"]    # use SBERT for section-level
                scores[section_name] = round(score, 1)
                feedback[section_name] = self._generate_feedback(section_name, score)
            except Exception as exc:
                logger.warning(
                    "Section scoring failed", section=section_name, error=str(exc)
                )

        if not scores:
            # Fallback — score the whole document
            result = similarity_engine.compute(resume_text, jd_text)
            scores["full_document"] = result["sbert_score"]
            feedback["full_document"] = "Section headers not detected; full-document match shown."

        strongest = max(scores, key=lambda k: scores[k]) if scores else "N/A"
        weakest   = min(scores, key=lambda k: scores[k]) if scores else "N/A"
        overall   = round(sum(scores.values()) / max(len(scores), 1), 1)

        logger.info(
            "Section analysis complete",
            sections=list(scores.keys()),
            strongest=strongest,
            weakest=weakest,
            overall=overall,
        )

        return SectionAnalysis(
            section_scores      =scores,
            section_feedback    =feedback,
            strongest_section   =strongest,
            weakest_section     =weakest,
            overall_section_score=overall,
        )

    @staticmethod
    def _generate_feedback(section: str, score: float) -> str:
        """Return human-readable feedback based on score tier."""
        thresholds = {
            "experience":     {"good": 70, "ok": 45},
            "education":      {"good": 60, "ok": 35},
            "skills":         {"good": 75, "ok": 50},
            "projects":       {"good": 65, "ok": 40},
            "certifications": {"good": 55, "ok": 30},
            "summary":        {"good": 60, "ok": 35},
            "achievements":   {"good": 55, "ok": 30},
        }
        t = thresholds.get(section, {"good": 65, "ok": 40})

        if score >= t["good"]:
            return f"✅ Strong match ({score:.0f}%). This section aligns well with the JD."
        elif score >= t["ok"]:
            return (
                f"⚠️ Moderate match ({score:.0f}%). "
                f"Enhance '{section}' with more JD-relevant keywords and detail."
            )
        else:
            return (
                f"❌ Weak match ({score:.0f}%). "
                f"Significantly improve '{section}' — it doesn't align with the job requirements."
            )


# Module-level singleton
section_analyzer = SectionAnalyzer()
