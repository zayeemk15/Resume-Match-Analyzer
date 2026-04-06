"""
tests/test_similarity.py — Unit tests for the SimilarityEngine
"""
import pytest
from backend.nlp.similarity_engine import SimilarityEngine


@pytest.fixture(scope="module")
def engine():
    return SimilarityEngine()


RESUME_SAMPLE = """
Python developer with 5 years of experience in machine learning and data engineering.
Proficient in TensorFlow, PyTorch, scikit-learn, pandas, and SQL.
Built scalable data pipelines using Apache Spark and Airflow.
Deployed ML models on AWS SageMaker and GCP Vertex AI.
Strong background in NLP, computer vision, and deep learning.
"""

JD_SIMILAR = """
We are looking for a Python Machine Learning Engineer with experience in TensorFlow,
PyTorch, and scikit-learn. The role involves building data pipelines, deploying models
on cloud platforms (AWS/GCP), and working with NLP and computer vision projects.
"""

JD_DIFFERENT = """
Marketing Manager role requiring strong communication skills, content creation,
social media management, brand strategy, and campaign analytics. 
No technical background required.
"""


class TestTfidfScore:
    def test_returns_float(self, engine):
        result = engine._tfidf_score(RESUME_SAMPLE, JD_SIMILAR)
        assert isinstance(result, float)

    def test_range_0_to_1(self, engine):
        score = engine._tfidf_score(RESUME_SAMPLE, JD_SIMILAR)
        assert 0.0 <= score <= 1.0

    def test_similar_texts_score_higher(self, engine):
        sim = engine._tfidf_score(RESUME_SAMPLE, JD_SIMILAR)
        diff = engine._tfidf_score(RESUME_SAMPLE, JD_DIFFERENT)
        assert sim > diff, f"Similar JD ({sim:.3f}) should score higher than different JD ({diff:.3f})"

    def test_identical_texts_near_1(self, engine):
        score = engine._tfidf_score(RESUME_SAMPLE, RESUME_SAMPLE)
        assert score > 0.95, f"Identical texts should score near 1.0, got {score:.3f}"

    def test_empty_text_no_crash(self, engine):
        score = engine._tfidf_score("", "some job description")
        assert 0.0 <= score <= 1.0


class TestSBERTScore:
    def test_returns_float(self, engine):
        result = engine._sbert_score(RESUME_SAMPLE, JD_SIMILAR)
        assert isinstance(result, float)

    def test_range_0_to_1(self, engine):
        score = engine._sbert_score(RESUME_SAMPLE, JD_SIMILAR)
        assert 0.0 <= score <= 1.0

    def test_similar_higher_than_different(self, engine):
        sim  = engine._sbert_score(RESUME_SAMPLE, JD_SIMILAR)
        diff = engine._sbert_score(RESUME_SAMPLE, JD_DIFFERENT)
        assert sim > diff, f"Expected similar JD ({sim:.3f}) > different JD ({diff:.3f})"

    def test_identical_texts_near_1(self, engine):
        score = engine._sbert_score("Hello world test", "Hello world test")
        assert score > 0.90, f"Identical texts should produce high SBERT score, got {score:.3f}"


class TestEnsembleScore:
    def test_compute_returns_dict(self, engine):
        result = engine.compute(RESUME_SAMPLE, JD_SIMILAR)
        assert isinstance(result, dict)

    def test_all_keys_present(self, engine):
        result = engine.compute(RESUME_SAMPLE, JD_SIMILAR)
        for key in ("tfidf_score", "sbert_score", "ensemble_score", "confidence"):
            assert key in result, f"Key '{key}' missing from result"

    def test_ensemble_in_percentage(self, engine):
        result = engine.compute(RESUME_SAMPLE, JD_SIMILAR)
        assert 0 <= result["ensemble_score"] <= 100

    def test_confidence_valid_value(self, engine):
        result = engine.compute(RESUME_SAMPLE, JD_SIMILAR)
        assert result["confidence"] in ("HIGH", "MEDIUM", "LOW")

    def test_similar_jd_scores_higher(self, engine):
        sim = engine.compute(RESUME_SAMPLE, JD_SIMILAR)["ensemble_score"]
        diff = engine.compute(RESUME_SAMPLE, JD_DIFFERENT)["ensemble_score"]
        assert sim > diff, f"Similar JD ({sim}) should rank higher than different JD ({diff})"


class TestRankResumes:
    def test_returns_sorted_list(self, engine):
        resumes = [RESUME_SAMPLE, "Basic resume with limited skills.", RESUME_SAMPLE[:500]]
        ranked = engine.rank_resumes(resumes, JD_SIMILAR)
        scores = [r["ensemble_score"] for r in ranked]
        assert scores == sorted(scores, reverse=True)

    def test_rank_field_assigned(self, engine):
        resumes = [RESUME_SAMPLE, "Entry level graduate with no experience."]
        ranked = engine.rank_resumes(resumes, JD_SIMILAR)
        for i, r in enumerate(ranked, start=1):
            assert r["rank"] == i
