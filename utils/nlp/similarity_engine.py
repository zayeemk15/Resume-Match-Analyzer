"""
nlp/similarity_engine.py — Three-tier similarity: TF-IDF, SBERT, BERT ensemble
"""
from __future__ import annotations
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from utils.core.config import settings
from utils.core.logging_config import get_logger
from tenacity import retry, stop_after_attempt, wait_exponential

logger = get_logger(__name__)


class SimilarityEngine:
    """
    Computes resume–JD similarity using three approaches:
      1. TF-IDF cosine similarity  (fast, keyword-based)
      2. Sentence-BERT embeddings  (semantic, phrase-level)
      3. BERT CLS token embeddings (deeper contextual)
    Returns a weighted ensemble score plus individual scores.
    """

    def __init__(self):
        self._sbert_model = None   # lazy-loaded
        self._bert_tokenizer = None
        self._bert_model_obj = None

    # ── Lazy Loaders ───────────────────────────────────────────
    def _get_sbert(self):
        if self._sbert_model is None:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading SBERT model", model=settings.sbert_model)
            self._sbert_model = SentenceTransformer(settings.sbert_model)
        return self._sbert_model

    def _get_bert(self):
        if self._bert_tokenizer is None:
            from transformers import AutoTokenizer, AutoModel
            logger.info("Loading BERT model", model=settings.bert_model)
            self._bert_tokenizer = AutoTokenizer.from_pretrained(settings.bert_model)
            self._bert_model_obj = AutoModel.from_pretrained(settings.bert_model)
        return self._bert_tokenizer, self._bert_model_obj

    # ── Public API ─────────────────────────────────────────────
    def compute(self, resume_text: str, jd_text: str) -> dict:
        """
        Compute all similarity scores and return structured result.

        Returns:
            {
              "tfidf_score": float,
              "sbert_score": float,
              "bert_score": float | None,
              "ensemble_score": float,          # 0–100
              "confidence": str,                # HIGH / MEDIUM / LOW
            }
        """
        tfidf = self._tfidf_score(resume_text, jd_text)
        sbert = self._sbert_score(resume_text, jd_text)
        bert  = self._bert_score(resume_text, jd_text)

        if bert is not None:
            ensemble = (
                tfidf * settings.tfidf_weight
                + sbert * settings.sbert_weight
                + bert  * settings.bert_weight
            )
        else:
            # Redistribute BERT weight to SBERT when BERT unavailable
            t_w = settings.tfidf_weight
            s_w = settings.sbert_weight + settings.bert_weight
            ensemble = tfidf * t_w + sbert * s_w

        ensemble_pct = round(float(ensemble) * 100, 2)

        confidence = "HIGH" if ensemble > 0.7 else "MEDIUM" if ensemble > 0.4 else "LOW"

        return {
            "tfidf_score":    round(float(tfidf) * 100, 2),
            "sbert_score":    round(float(sbert) * 100, 2),
            "bert_score":     round(float(bert)  * 100, 2) if bert is not None else None,
            "ensemble_score": ensemble_pct,
            "confidence":     confidence,
        }

    # ── Individual Scorers ─────────────────────────────────────
    def _tfidf_score(self, text_a: str, text_b: str) -> float:
        """TF-IDF cosine similarity (very fast, no GPU needed)."""
        try:
            vectorizer = TfidfVectorizer(
                ngram_range=(1, 2),
                max_features=10_000,
                sublinear_tf=True,
            )
            matrix = vectorizer.fit_transform([text_a, text_b])
            score = cosine_similarity(matrix[0:1], matrix[1:2])[0][0]
            return float(np.clip(score, 0.0, 1.0))
        except Exception as exc:
            logger.error("TF-IDF score failed", error=str(exc))
            return 0.0

    def _sbert_score(self, text_a: str, text_b: str) -> float:
        """Sentence-BERT cosine similarity (semantic understanding)."""
        try:
            model = self._get_sbert()
            # Truncate to first 512 tokens worth of chars to keep latency low
            emb_a, emb_b = model.encode(
                [text_a[:3000], text_b[:3000]],
                convert_to_numpy=True,
                normalize_embeddings=True,
            )
            score = float(np.dot(emb_a, emb_b))
            return float(np.clip(score, 0.0, 1.0))
        except Exception as exc:
            logger.error("SBERT score failed", error=str(exc))
            return 0.0

    def _bert_score(self, text_a: str, text_b: str) -> float | None:
        """BERT CLS-token cosine similarity (optional, heavier)."""
        try:
            import torch
            tokenizer, model = self._get_bert()
            model.eval()
            with torch.no_grad():
                def _encode(text: str) -> np.ndarray:
                    inputs = tokenizer(
                        text[:512],
                        return_tensors="pt",
                        truncation=True,
                        max_length=512,
                        padding=True,
                    )
                    output = model(**inputs)
                    cls = output.last_hidden_state[:, 0, :].squeeze().numpy()
                    return cls / (np.linalg.norm(cls) + 1e-8)

                vec_a = _encode(text_a)
                vec_b = _encode(text_b)
                score = float(np.dot(vec_a, vec_b))
            return float(np.clip(score, 0.0, 1.0))
        except Exception as exc:
            logger.warning("BERT score unavailable (skipped)", error=str(exc))
            return None

    def rank_resumes(self, resumes: list[str], jd_text: str) -> list[dict]:
        """
        Rank multiple resumes against one JD.

        Returns:
            List of dicts sorted by ensemble_score descending.
        """
        results = []
        for idx, resume in enumerate(resumes):
            scores = self.compute(resume, jd_text)
            scores["rank"] = idx  # original index
            results.append(scores)

        results.sort(key=lambda x: x["ensemble_score"], reverse=True)
        for rank, result in enumerate(results, start=1):
            result["rank"] = rank
        return results


# Module-level singleton
similarity_engine = SimilarityEngine()
