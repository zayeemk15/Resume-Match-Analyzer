"""
nlp/ats_simulator.py — Applicant Tracking System score simulator
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from utils.nlp.skill_extractor import skill_extractor
from utils.core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class ATSReport:
    ats_score: float                     # 0–100
    keyword_density_score: float         # 0–100
    format_score: float                  # 0–100
    keyword_match_score: float           # 0–100
    matched_keywords: list[str]
    missing_keywords: list[str]
    format_feedback: list[str]
    improvement_tips: list[str]


class ATSSimulator:
    """
    Simulates how an ATS system would score a resume against a JD.
    Checks:
    1. Keyword density and match rate
    2. Formatting compliance (section headers, bullet points, dates)
    3. ATS-unfriendly patterns (tables, images, columns)
    """

    # ATS-friendly signals
    DATE_PATTERN       = re.compile(r"\b(20\d{2}|19\d{2})\b")
    BULLET_PATTERN     = re.compile(r"^[\-\•\*▪▸►]\s", re.MULTILINE)
    EMAIL_PATTERN      = re.compile(r"[\w.\-]+@[\w.\-]+\.\w+")
    PHONE_PATTERN      = re.compile(r"\+?\d[\d\s\-\(\)]{7,}\d")
    ACTION_VERBS       = {
        "developed", "built", "designed", "implemented", "led", "managed",
        "improved", "optimized", "reduced", "increased", "created", "engineered",
        "deployed", "integrated", "architected", "automated", "mentored",
    }
    REQUIRED_SECTIONS  = {"experience", "education", "skills"}
    ATS_BAD_PATTERNS   = ["table", "text box", "header footer", "image"]

    def score(self, resume_text: str, jd_text: str) -> ATSReport:
        """
        Compute ATS score and return detailed breakdown.

        Weights:
          - Keyword match:  50%
          - Format:         30%
          - Keyword density:20%
        """
        kw_match, matched, missing = self._keyword_match(resume_text, jd_text)
        fmt_score, fmt_feedback    = self._format_score(resume_text)
        density_score              = self._keyword_density_score(resume_text, matched)
        tips                       = self._improvement_tips(missing, fmt_feedback)

        ats = (kw_match * 0.50) + (fmt_score * 0.30) + (density_score * 0.20)

        logger.info(
            "ATS simulation complete",
            ats_score=round(ats, 1),
            kw_match=round(kw_match, 1),
            fmt_score=round(fmt_score, 1),
        )

        return ATSReport(
            ats_score             = round(ats, 2),
            keyword_density_score = round(density_score, 2),
            format_score          = round(fmt_score, 2),
            keyword_match_score   = round(kw_match, 2),
            matched_keywords      = sorted(matched),
            missing_keywords      = sorted(missing)[:20],
            format_feedback       = fmt_feedback,
            improvement_tips      = tips,
        )

    # ── Private Methods ────────────────────────────────────────
    def _keyword_match(
        self, resume_text: str, jd_text: str
    ) -> tuple[float, list[str], list[str]]:
        """Score based on % of JD keywords present in resume."""
        jd_result = skill_extractor.extract(jd_text)
        jd_keywords = set(jd_result.all_found)

        # Also extract plain word tokens from JD (important non-skill words)
        jd_words = {
            w.lower() for w in re.findall(r"\b[a-zA-Z]{3,}\b", jd_text)
            if w.lower() not in _STOP_WORDS
        }
        jd_all = jd_keywords | jd_words

        resume_lower = resume_text.lower()
        matched = [kw for kw in jd_all if re.search(rf"\b{re.escape(kw)}\b", resume_lower)]
        missing = [kw for kw in jd_all if kw not in set(matched)]

        score = (len(matched) / max(len(jd_all), 1)) * 100
        return score, matched, missing

    def _format_score(self, resume_text: str) -> tuple[float, list[str]]:
        """Score resume formatting for ATS compliance."""
        score = 0.0
        feedback: list[str] = []

        # Check sections (30 pts)
        lower = resume_text.lower()
        found_sections = sum(1 for s in self.REQUIRED_SECTIONS if s in lower)
        section_score = (found_sections / len(self.REQUIRED_SECTIONS)) * 30
        score += section_score
        if found_sections < len(self.REQUIRED_SECTIONS):
            missing = [s for s in self.REQUIRED_SECTIONS if s not in lower]
            feedback.append(f"Missing required sections: {', '.join(missing)}")

        # Check dates (20 pts)
        dates = self.DATE_PATTERN.findall(resume_text)
        if len(dates) >= 2:
            score += 20
        else:
            feedback.append("Add dates to Experience and Education sections.")

        # Check bullets (20 pts)
        bullets = self.BULLET_PATTERN.findall(resume_text)
        if len(bullets) >= 5:
            score += 20
        elif len(bullets) >= 2:
            score += 10
            feedback.append("Use more bullet points to describe accomplishments.")
        else:
            feedback.append("Use bullet points for easy ATS parsing.")

        # Check contact info (15 pts)
        has_email = bool(self.EMAIL_PATTERN.search(resume_text))
        has_phone = bool(self.PHONE_PATTERN.search(resume_text))
        if has_email: score += 8
        else: feedback.append("Add an email address.")
        if has_phone: score += 7
        else: feedback.append("Add a phone number.")

        # Action verbs (15 pts)
        words_lower = set(re.findall(r"\b\w+\b", resume_text.lower()))
        found_verbs = self.ACTION_VERBS & words_lower
        verb_score = min(len(found_verbs) / 5 * 15, 15)
        score += verb_score
        if len(found_verbs) < 3:
            feedback.append("Use strong action verbs (built, developed, optimized, led).")

        return min(score, 100.0), feedback

    def _keyword_density_score(self, resume_text: str, matched: list[str]) -> float:
        """Score based on keyword density (not keyword stuffing)."""
        word_count = max(len(resume_text.split()), 1)
        density = len(matched) / word_count
        # Ideal density: 2%–8%
        if 0.02 <= density <= 0.08:
            return 100.0
        elif density < 0.02:
            return density / 0.02 * 100
        else:
            # Penalise stuffing
            return max(100 - (density - 0.08) / 0.02 * 20, 40.0)

    def _improvement_tips(
        self, missing_kw: list[str], fmt_issues: list[str]
    ) -> list[str]:
        tips = []
        if missing_kw[:5]:
            tips.append(
                f"Add these missing keywords naturally: "
                f"{', '.join(missing_kw[:5])}"
            )
        tips.extend(fmt_issues[:4])
        if not tips:
            tips.append("Great ATS compliance! Minor tweaks can push score to 100.")
        return tips


_STOP_WORDS = {
    "the", "and", "for", "are", "you", "with", "this", "that", "have",
    "will", "work", "our", "your", "team", "role", "able", "must",
    "from", "into", "they", "who", "what", "when", "where", "which",
    "their", "about", "would", "other", "been", "were", "should",
}

# Module-level singleton
ats_simulator = ATSSimulator()
