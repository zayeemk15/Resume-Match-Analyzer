"""
nlp/llm_suggestions.py — LLM-powered resume improvement suggestions
Falls back to rule-based suggestions if OpenAI key not set.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from utils.core.config import settings
from utils.core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class SuggestionReport:
    resume_bullets: list[str]          # 5 improved bullet points
    keyword_suggestions: list[str]     # keywords to add
    summary_rewrite: str               # improved professional summary
    overall_advice: str                # one paragraph of strategic advice
    used_llm: bool = False


class LLMSuggestions:
    """
    Generates actionable resume improvement suggestions.
    Uses OpenAI GPT when API key is set, otherwise falls back to rule-based engine.
    """

    def generate(
        self,
        resume_text: str,
        jd_text: str,
        missing_skills: list[str],
        match_score: float,
    ) -> SuggestionReport:
        if settings.effective_use_llm:
            try:
                return self._openai_generate(resume_text, jd_text, missing_skills, match_score)
            except Exception as exc:
                logger.warning("OpenAI call failed, falling back to rules", error=str(exc))

        return self._rule_based_generate(resume_text, jd_text, missing_skills, match_score)

    # ── OpenAI Path ────────────────────────────────────────────
    def _openai_generate(
        self,
        resume_text: str,
        jd_text: str,
        missing_skills: list[str],
        match_score: float,
    ) -> SuggestionReport:
        from openai import OpenAI
        client = OpenAI(api_key=settings.openai_api_key)

        prompt = f"""You are an expert career coach and ATS optimization specialist.

RESUME (first 1500 chars):
{resume_text[:1500]}

JOB DESCRIPTION (first 1000 chars):
{jd_text[:1000]}

CURRENT MATCH SCORE: {match_score:.1f}%
MISSING SKILLS: {", ".join(missing_skills[:10])}

Please provide:
1. FIVE improved resume bullet points (STAR format, with metrics)
2. TEN keywords to add naturally to the resume
3. A rewritten professional summary (3 sentences, keyword-rich)
4. One paragraph of strategic advice to improve the match score

Format your response as JSON with keys:
"bullets" (list of 5 strings),
"keywords" (list of 10 strings),
"summary" (string),
"advice" (string)
"""
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=1200,
        )
        import json
        data = json.loads(response.choices[0].message.content)
        return SuggestionReport(
            resume_bullets    =data.get("bullets", []),
            keyword_suggestions=data.get("keywords", []),
            summary_rewrite   =data.get("summary", ""),
            overall_advice    =data.get("advice", ""),
            used_llm          =True,
        )

    # ── Rule-Based Fallback ────────────────────────────────────
    def _rule_based_generate(
        self,
        resume_text: str,
        jd_text: str,
        missing_skills: list[str],
        match_score: float,
    ) -> SuggestionReport:
        """Generate suggestions using heuristics, no API call needed."""

        # Extract top JD action verbs to suggest
        import re
        action_verbs = [
            "Developed", "Engineered", "Optimized", "Architected", "Deployed",
            "Led", "Designed", "Automated", "Integrated", "Reduced",
        ]

        bullets = [
            f"{action_verbs[i % len(action_verbs)]} {skill}-based solutions, "
            f"reducing processing time by 30% and improving team productivity."
            for i, skill in enumerate(missing_skills[:5])
        ] or [
            "Developed scalable microservices reducing API latency by 40%.",
            "Led cross-functional team of 5, delivering project 2 weeks ahead of schedule.",
            "Automated CI/CD pipeline, cutting deployment time from 2 hours to 15 minutes.",
            "Optimized database queries, improving performance by 60% on 10M+ records.",
            "Built end-to-end ML pipeline processing 1M+ events daily with 99.9% uptime.",
        ]

        keywords = missing_skills[:10] or [
            "machine learning", "cloud architecture", "microservices",
            "data pipeline", "kubernetes", "agile", "system design",
        ]

        # Build a professional summary hint
        jd_words = re.findall(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b", jd_text)
        role_hint = jd_words[0] if jd_words else "Software Engineer"

        summary = (
            f"Results-driven professional with proven expertise in "
            f"{', '.join(missing_skills[:3]) if missing_skills else 'software development and data engineering'}. "
            f"Adept at building scalable systems and collaborating in agile environments. "
            f"Passionate about delivering high-impact solutions that align with "
            f"{role_hint} requirements."
        )

        if match_score >= 70:
            advice = (
                "Your resume is a strong match! Fine-tune by adding quantifiable metrics "
                "to each bullet point and ensuring all listed skills appear exactly as written in the JD."
            )
        elif match_score >= 45:
            advice = (
                f"Your match score is moderate ({match_score:.0f}%). Focus on: "
                f"(1) adding missing skills ({', '.join(missing_skills[:3])}), "
                f"(2) rewriting experience bullets with STAR format and metrics, "
                f"(3) mirroring the JD language in your summary section."
            )
        else:
            advice = (
                f"Your match score is low ({match_score:.0f}%). Major improvements needed: "
                f"(1) significantly upskill in {', '.join(missing_skills[:4])}, "
                f"(2) overhaul your summary and skills sections to mirror the JD, "
                f"(3) consider taking an online course or project to demonstrate experience "
                f"in the core required technologies."
            )

        return SuggestionReport(
            resume_bullets     =bullets,
            keyword_suggestions=keywords,
            summary_rewrite    =summary,
            overall_advice     =advice,
            used_llm           =False,
        )


# Module-level singleton
llm_suggestions = LLMSuggestions()
