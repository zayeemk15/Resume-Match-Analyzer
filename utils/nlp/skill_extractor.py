"""
nlp/skill_extractor.py — Skill detection using keyword matching + NER
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from dataclasses import dataclass, field
from utils.core.logging_config import get_logger

logger = get_logger(__name__)

_DB_PATH = Path(__file__).parent.parent / "data" / "skills_db.json"


@dataclass
class SkillExtractionResult:
    found_skills: dict[str, list[str]]   = field(default_factory=dict)  # category → [skill]
    all_found: list[str]                  = field(default_factory=list)
    skill_score: float                    = 0.0


class SkillExtractor:
    """
    Extracts skills from free text using:
    1. Keyword / phrase matching against skills_db.json
    2. spaCy NER for ORG/PRODUCT entities (technology names)
    """

    def __init__(self):
        self._skills_db: dict[str, list[str]] = {}
        self._flat_skills: list[tuple[str, str]] = []  # (category, skill)
        self._nlp = None
        self._loaded = False

    def _ensure_loaded(self):
        if self._loaded:
            return
        if _DB_PATH.exists():
            with open(_DB_PATH, "r", encoding="utf-8") as f:
                self._skills_db = json.load(f)
        else:
            # Fallback inline minimal skill set if file missing
            self._skills_db = _MINIMAL_SKILLS_DB
            logger.warning("skills_db.json not found, using minimal fallback")

        # Build sorted flat list (longest phrases first to avoid partial matches)
        for category, skills in self._skills_db.items():
            for skill in skills:
                self._flat_skills.append((category, skill.lower()))
        self._flat_skills.sort(key=lambda x: len(x[1]), reverse=True)
        self._loaded = True

    def _get_nlp(self):
        if self._nlp is None:
            try:
                import spacy
                self._nlp = spacy.load("en_core_web_sm")
            except Exception:
                self._nlp = False
        return self._nlp

    # ── Public API ─────────────────────────────────────────────
    def extract(self, text: str) -> SkillExtractionResult:
        """Extract skills from text, return categorized result."""
        self._ensure_loaded()
        text_lower = text.lower()
        found: dict[str, set[str]] = {}

        for category, skill in self._flat_skills:
            # Word-boundary match to avoid partial word matches
            pattern = rf"\b{re.escape(skill)}\b"
            if re.search(pattern, text_lower):
                found.setdefault(category, set()).add(skill)

        # Supplement with NER
        ner_skills = self._ner_extract(text, text_lower)
        for skill in ner_skills:
            found.setdefault("ner_detected", set()).add(skill)

        # Convert sets → sorted lists
        found_lists: dict[str, list[str]] = {k: sorted(v) for k, v in found.items()}
        all_found = sorted({s for skills in found_lists.values() for s in skills})

        # Skill score = unique found / total in DB (capped at 1.0)
        total = sum(len(v) for v in self._skills_db.values())
        score = min(len(all_found) / max(total, 1), 1.0)

        return SkillExtractionResult(
            found_skills=found_lists,
            all_found=all_found,
            skill_score=round(score, 4),
        )

    def _ner_extract(self, text: str, text_lower: str) -> list[str]:
        """Use spaCy NER to find technology/product names not in DB."""
        nlp = self._get_nlp()
        if not nlp:
            return []
        tech_entities = []
        try:
            doc = nlp(text[:5000])
            for ent in doc.ents:
                if ent.label_ in ("ORG", "PRODUCT", "WORK_OF_ART"):
                    name = ent.text.strip().lower()
                    if 2 < len(name) < 40 and name not in text_lower:
                        tech_entities.append(name)
        except Exception as exc:
            logger.warning("NER extraction failed", error=str(exc))
        return tech_entities

    def get_all_skills_for_category(self, category: str) -> list[str]:
        """Return all skills in a given category from the DB."""
        self._ensure_loaded()
        return self._skills_db.get(category, [])

    def get_categories(self) -> list[str]:
        self._ensure_loaded()
        return list(self._skills_db.keys())


# ── Minimal fallback skill DB (used if JSON file missing) ──────
_MINIMAL_SKILLS_DB: dict[str, list[str]] = {
    "Programming Languages": [
        "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
        "r", "scala", "kotlin", "swift", "php", "ruby", "matlab",
    ],
    "Web Frameworks": [
        "react", "angular", "vue", "django", "flask", "fastapi", "node.js",
        "express", "spring boot", "laravel", "rails", "next.js", "nuxt",
    ],
    "Databases": [
        "sql", "mysql", "postgresql", "mongodb", "redis", "elasticsearch",
        "cassandra", "sqlite", "oracle", "dynamodb", "neo4j",
    ],
    "Cloud & DevOps": [
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ansible",
        "jenkins", "github actions", "ci/cd", "linux", "bash",
    ],
    "Machine Learning & AI": [
        "machine learning", "deep learning", "nlp", "computer vision",
        "tensorflow", "pytorch", "keras", "scikit-learn", "pandas", "numpy",
        "hugging face", "bert", "gpt", "llm", "langchain", "openai",
        "transformers", "spacy", "nltk", "xgboost", "lightgbm",
    ],
    "Data Engineering": [
        "spark", "hadoop", "kafka", "airflow", "dbt", "snowflake",
        "databricks", "etl", "data pipeline", "bigquery",
    ],
    "Soft Skills": [
        "leadership", "communication", "teamwork", "problem solving",
        "critical thinking", "collaboration", "agile", "scrum", "project management",
    ],
    "Certifications": [
        "aws certified", "google certified", "azure certified", "pmp",
        "cpa", "cissp", "comptia", "tensorflow developer certificate",
    ],
}


# Module-level singleton
skill_extractor = SkillExtractor()
