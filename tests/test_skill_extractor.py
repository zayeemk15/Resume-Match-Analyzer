"""
tests/test_skill_extractor.py — Unit tests for SkillExtractor
"""
import pytest
from backend.nlp.skill_extractor import SkillExtractor


@pytest.fixture(scope="module")
def extractor():
    return SkillExtractor()


TECH_RESUME = """
Software Engineer with expertise in Python, Java, and TypeScript.
Worked with React, FastAPI, and Django for web development.
Managed PostgreSQL and MongoDB databases.
Deployed applications on AWS EC2, S3, and used Docker and Kubernetes.
Experience with TensorFlow, PyTorch, and scikit-learn for ML projects.
Familiar with Git, GitHub Actions, and CI/CD pipelines.
"""

SOFT_RESUME = """
Project Manager with excellent communication and leadership skills.
Led cross-functional teams using Agile and Scrum methodologies.
Strong problem solving, time management, and critical thinking abilities.
"""


class TestSkillExtraction:
    def test_returns_result_object(self, extractor):
        result = extractor.extract(TECH_RESUME)
        assert result is not None

    def test_python_detected(self, extractor):
        result = extractor.extract(TECH_RESUME)
        assert "python" in result.all_found

    def test_sql_detected(self, extractor):
        result = extractor.extract(TECH_RESUME)
        assert any("sql" in s for s in result.all_found) or "postgresql" in result.all_found

    def test_docker_detected(self, extractor):
        result = extractor.extract(TECH_RESUME)
        assert "docker" in result.all_found

    def test_tensorflow_detected(self, extractor):
        result = extractor.extract(TECH_RESUME)
        assert "tensorflow" in result.all_found

    def test_soft_skills_detected(self, extractor):
        result = extractor.extract(SOFT_RESUME)
        found_lower = [s.lower() for s in result.all_found]
        assert any(s in found_lower for s in ["leadership", "communication", "teamwork", "agile", "scrum"])

    def test_found_skills_categorized(self, extractor):
        result = extractor.extract(TECH_RESUME)
        assert isinstance(result.found_skills, dict)
        assert len(result.found_skills) > 0

    def test_skill_score_in_range(self, extractor):
        result = extractor.extract(TECH_RESUME)
        assert 0.0 <= result.skill_score <= 1.0

    def test_empty_text_no_crash(self, extractor):
        result = extractor.extract("")
        assert result.all_found == []
        assert result.skill_score == 0.0


class TestSkillGapAnalyzer:
    def test_identifies_missing_skills(self):
        from backend.nlp.skill_gap_analyzer import SkillGapAnalyzer
        analyzer = SkillGapAnalyzer()

        resume = "Python developer with pandas and numpy experience."
        jd = "Looking for Python, Kubernetes, Spark, and Kafka expert."

        report = analyzer.analyze(resume, jd)
        missing = [s.lower() for s in report.all_missing]
        # Kubernetes, Spark, Kafka should be in missing
        assert any(m in missing for m in ["kubernetes", "spark", "kafka"]), \
            f"Expected k8s/spark/kafka in missing, got: {missing[:10]}"

    def test_coverage_score_range(self):
        from backend.nlp.skill_gap_analyzer import SkillGapAnalyzer
        analyzer = SkillGapAnalyzer()
        report = analyzer.analyze(
            "Python, React, Docker, AWS", "Python, React, Docker, AWS"
        )
        assert 0 <= report.coverage_score <= 100

    def test_perfect_match_high_coverage(self):
        from backend.nlp.skill_gap_analyzer import SkillGapAnalyzer
        analyzer = SkillGapAnalyzer()
        text = "Python Java TensorFlow AWS Docker Kubernetes PostgreSQL"
        report = analyzer.analyze(text, text)
        assert report.all_missing == [], f"Identical texts should have no missing skills, got {report.all_missing}"

    def test_priority_gaps_ordered(self):
        from backend.nlp.skill_gap_analyzer import SkillGapAnalyzer
        analyzer = SkillGapAnalyzer()
        report = analyzer.analyze(
            "Communication and teamwork skills.",
            "Python TensorFlow PyTorch AWS Kubernetes Leadership"
        )
        if report.priority_gaps:
            priorities = [g["priority"] for g in report.priority_gaps]
            # HIGH priority gaps should come before MEDIUM/LOW
            high_idx = [i for i, p in enumerate(priorities) if p == "HIGH"]
            low_idx  = [i for i, p in enumerate(priorities) if p == "LOW"]
            if high_idx and low_idx:
                assert max(high_idx) < min(low_idx), "HIGH priority gaps should appear before LOW"
