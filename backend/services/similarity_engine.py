import logging
import numpy as np
from typing import Dict, List, Optional, Tuple
from sklearn.metrics.pairwise import cosine_similarity
from .text_preprocessor import TextPreprocessor

logger = logging.getLogger(__name__)

# Global cached model instance to ensure loading once per application process
_CACHED_MODEL = None
_MODEL_LOAD_ATTEMPTED = False
_MODEL_LOAD_ERROR = None


def is_model_loaded() -> bool:
    """Returns True if the embedding model is already loaded in memory."""
    return _CACHED_MODEL is not None


def get_embedding_model(model_name: str = "sentence-transformers/all-MiniLM-L6-v2", allow_blocking: bool = False):
    """
    Returns SentenceTransformer model singleton.
    If allow_blocking is False and model is not yet loaded into memory,
    returns None immediately so that requests utilize TF-IDF fallback without hanging.
    """
    global _CACHED_MODEL, _MODEL_LOAD_ATTEMPTED, _MODEL_LOAD_ERROR
    if _CACHED_MODEL is not None:
        return _CACHED_MODEL
    
    if not allow_blocking:
        return None

    if _MODEL_LOAD_ATTEMPTED and _MODEL_LOAD_ERROR is not None:
        return None

    _MODEL_LOAD_ATTEMPTED = True
    try:
        from sentence_transformers import SentenceTransformer
        logger.info(f"Loading embedding model: {model_name}...")
        _CACHED_MODEL = SentenceTransformer(model_name)
        logger.info("Embedding model loaded successfully.")
        return _CACHED_MODEL
    except Exception as e:
        _MODEL_LOAD_ERROR = str(e)
        logger.error(f"Failed to load SentenceTransformer ({model_name}): {e}")
        return None


class SimilarityEngine:
    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        semantic_weight: float = 0.40,
        required_skill_weight: float = 0.40,
        preferred_skill_weight: float = 0.20
    ):
        self.model_name = model_name
        self.semantic_weight = semantic_weight
        self.required_skill_weight = required_skill_weight
        self.preferred_skill_weight = preferred_skill_weight
        self.preprocessor = TextPreprocessor()

    @property
    def is_model_ready(self) -> bool:
        return get_embedding_model(self.model_name) is not None

    def compute_tfidf_fallback(self, resume_text: str, jd_text: str) -> float:
        """Fallback cosine similarity using scikit-learn TF-IDF if neural model is unavailable."""
        from sklearn.feature_extraction.text import TfidfVectorizer
        try:
            vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
            tfidf_matrix = vectorizer.fit_transform([resume_text, jd_text])
            score = float(cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0])
            return float(np.clip(score * 100.0, 0.0, 100.0))
        except Exception as e:
            logger.warning(f"TF-IDF fallback calculation error: {e}")
            return 0.0

    def compute_semantic_similarity(self, resume_text: str, jd_text: str) -> float:
        """
        Computes chunk-aware and document-level semantic similarity.
        Splits both documents into meaningful chunks to overcome model token limits
        and calculates hybrid alignment.
        """
        model = get_embedding_model(self.model_name)
        if model is None:
            logger.warning("Neural model unavailable, falling back to TF-IDF cosine similarity.")
            return self.compute_tfidf_fallback(resume_text, jd_text)

        try:
            resume_chunks = self.preprocessor.create_overlapping_chunks(resume_text)
            jd_chunks = self.preprocessor.create_overlapping_chunks(jd_text)

            if not resume_chunks or not jd_chunks:
                return 0.0

            # Encode chunks
            resume_embeddings = model.encode(resume_chunks, show_progress_bar=False, normalize_embeddings=True)
            jd_embeddings = model.encode(jd_chunks, show_progress_bar=False, normalize_embeddings=True)

            # Similarity matrix between all pairs of chunks (N_resume x M_jd)
            sim_matrix = cosine_similarity(resume_embeddings, jd_embeddings)

            # For each JD requirement chunk, what is the best matching resume chunk?
            best_resume_matches_per_jd = np.max(sim_matrix, axis=0)
            avg_jd_coverage = float(np.mean(best_resume_matches_per_jd))

            # Also encode overall document text representations (truncated to model safe limit)
            doc_embeddings = model.encode(
                [resume_text[:2000], jd_text[:2000]],
                show_progress_bar=False,
                normalize_embeddings=True
            )
            doc_similarity = float(cosine_similarity(doc_embeddings[0:1], doc_embeddings[1:2])[0][0])

            # Composite semantic score: 65% chunk coverage + 35% global representation
            composite = 0.65 * avg_jd_coverage + 0.35 * doc_similarity

            # Rescale slightly from raw cosine similarity [-1, 1] / [0, 1] to human-friendly alignment [0, 100]
            # MiniLM cosine similarity typically ranges from 0.2 (unrelated) to 0.85 (nearly identical)
            scaled_score = max(0.0, min(100.0, composite * 100.0))
            return round(scaled_score, 2)
        except Exception as e:
            logger.error(f"Semantic similarity calculation failed: {e}")
            return self.compute_tfidf_fallback(resume_text, jd_text)

    def calculate_overall_score(
        self,
        semantic_score: float,
        required_coverage: float,
        preferred_coverage: Optional[float]
    ) -> Tuple[float, Dict[str, float]]:
        """
        Calculates explainable weighted alignment score with dynamic renormalization.
        If preferred skills are absent, renormalizes semantic and required weights.
        Clamps all values strictly between 0 and 100.
        """
        semantic_score = float(np.clip(semantic_score, 0.0, 100.0))
        required_coverage = float(np.clip(required_coverage, 0.0, 100.0))

        if preferred_coverage is not None:
            preferred_coverage = float(np.clip(preferred_coverage, 0.0, 100.0))
            total_w = self.semantic_weight + self.required_skill_weight + self.preferred_skill_weight
            norm_sem = self.semantic_weight / total_w
            norm_req = self.required_skill_weight / total_w
            norm_pref = self.preferred_skill_weight / total_w

            overall = (
                norm_sem * semantic_score +
                norm_req * required_coverage +
                norm_pref * preferred_coverage
            )
            weights = {
                "semantic_weight": round(norm_sem, 2),
                "required_skill_weight": round(norm_req, 2),
                "preferred_skill_weight": round(norm_pref, 2)
            }
        else:
            # Renormalize without preferred skills
            total_w = self.semantic_weight + self.required_skill_weight
            norm_sem = self.semantic_weight / total_w
            norm_req = self.required_skill_weight / total_w

            overall = (
                norm_sem * semantic_score +
                norm_req * required_coverage
            )
            weights = {
                "semantic_weight": round(norm_sem, 2),
                "required_skill_weight": round(norm_req, 2),
                "preferred_skill_weight": 0.0
            }

        clamped_overall = round(float(np.clip(overall, 0.0, 100.0)), 2)
        return clamped_overall, weights
