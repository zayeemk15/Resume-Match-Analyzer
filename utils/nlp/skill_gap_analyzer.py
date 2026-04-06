"""
nlp/skill_gap_analyzer.py — Identify missing skills and generate recommendations
"""
from __future__ import annotations
from dataclasses import dataclass, field
from utils.nlp.skill_extractor import skill_extractor, SkillExtractionResult
from utils.core.logging_config import get_logger

logger = get_logger(__name__)

# Learning resource URLs per category (static mapping for MVP)
LEARNING_RESOURCES: dict[str, str] = {
    "Programming Languages": "https://www.learnpython.org / https://exercism.org",
    "Web Frameworks":        "https://reactjs.org/docs / https://fastapi.tiangolo.com",
    "Databases":             "https://use-the-index-luke.com / https://sqlzoo.net",
    "Cloud & DevOps":        "https://acloudguru.com / https://learn.microsoft.com/azure",
    "Machine Learning & AI": "https://fast.ai / https://huggingface.co/learn",
    "Data Engineering":      "https://www.databricks.com/learn / https://airflow.apache.org",
    "Soft Skills":           "https://www.coursera.org/professional-certificates",
    "Certifications":        "https://www.credly.com / https://training.linuxfoundation.org",
    "ner_detected":          "https://leetcode.com / https://roadmap.sh",
}


@dataclass
class SkillGapReport:
    resume_skills: dict[str, list[str]]
    jd_skills: dict[str, list[str]]
    missing_by_category: dict[str, list[str]]
    all_missing: list[str]
    all_resume_skills: list[str]
    all_jd_skills: list[str]
    coverage_score: float          # 0–100  (% of JD skills present in resume)
    priority_gaps: list[dict]      # top-N ranked by JD frequency
    learning_resources: dict[str, str]


class SkillGapAnalyzer:
    """
    Compares skills found in a resume vs skills required in a JD.
    Produces a gap report with priority rankings and learning resources.
    """

    def analyze(
        self,
        resume_text: str,
        jd_text: str,
        top_n: int = 15,
    ) -> SkillGapReport:
        """
        Run full gap analysis.

        Args:
            resume_text: Cleaned resume text.
            jd_text:     Cleaned JD text.
            top_n:       Maximum priority gap entries to return.

        Returns:
            SkillGapReport with all gap details and recommendations.
        """
        resume_result: SkillExtractionResult = skill_extractor.extract(resume_text)
        jd_result:     SkillExtractionResult = skill_extractor.extract(jd_text)

        resume_set = set(resume_result.all_found)
        jd_set     = set(jd_result.all_found)

        missing = jd_set - resume_set

        # Group missing by category
        missing_by_cat: dict[str, list[str]] = {}
        for category, skills in jd_result.found_skills.items():
            cat_missing = [s for s in skills if s in missing]
            if cat_missing:
                missing_by_cat[category] = sorted(cat_missing)

        # Coverage score
        coverage = (
            (len(jd_set) - len(missing)) / len(jd_set) * 100
            if jd_set else 100.0
        )

        # Priority gaps — order by category importance then alphabetically
        priority_order = [
            "Machine Learning & AI", "Cloud & DevOps", "Programming Languages",
            "Web Frameworks", "Databases", "Data Engineering",
            "Soft Skills", "Certifications", "ner_detected",
        ]
        priority_gaps: list[dict] = []
        for cat in priority_order:
            for skill in missing_by_cat.get(cat, []):
                if len(priority_gaps) >= top_n:
                    break
                priority_gaps.append({
                    "skill":    skill,
                    "category": cat,
                    "priority": "HIGH" if cat in priority_order[:4] else "MEDIUM",
                    "resource": LEARNING_RESOURCES.get(cat, "https://www.coursera.org"),
                })

        # Fill remaining slots from other categories
        for cat, skills in missing_by_cat.items():
            if cat not in priority_order:
                for skill in skills:
                    if len(priority_gaps) >= top_n:
                        break
                    priority_gaps.append({
                        "skill":    skill,
                        "category": cat,
                        "priority": "LOW",
                        "resource": LEARNING_RESOURCES.get(cat, "https://www.coursera.org"),
                    })

        resources: dict[str, str] = {
            cat: LEARNING_RESOURCES.get(cat, "https://www.coursera.org")
            for cat in missing_by_cat
        }

        logger.info(
            "Skill gap analysis complete",
            total_jd_skills=len(jd_set),
            missing=len(missing),
            coverage=f"{coverage:.1f}%",
        )

        return SkillGapReport(
            resume_skills     =resume_result.found_skills,
            jd_skills         =jd_result.found_skills,
            missing_by_category=missing_by_cat,
            all_missing       =sorted(missing),
            all_resume_skills =sorted(resume_set),
            all_jd_skills     =sorted(jd_set),
            coverage_score    =round(coverage, 2),
            priority_gaps     =priority_gaps,
            learning_resources=resources,
        )


# Module-level singleton
skill_gap_analyzer = SkillGapAnalyzer()
