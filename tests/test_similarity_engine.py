import pytest
from backend.services.similarity_engine import SimilarityEngine
from backend.services.text_preprocessor import TextPreprocessor


class TestSimilarityEngine:
    def setup_method(self):
        self.engine = SimilarityEngine(
            semantic_weight=0.40,
            required_skill_weight=0.40,
            preferred_skill_weight=0.20
        )
        self.preprocessor = TextPreprocessor()

    def test_overall_score_with_preferred_skills(self):
        # 40% semantic (80), 40% req (90), 20% pref (60)
        # Expected: 0.40*80 + 0.40*90 + 0.20*60 = 32 + 36 + 12 = 80.0
        score, weights = self.engine.calculate_overall_score(
            semantic_score=80.0,
            required_coverage=90.0,
            preferred_coverage=60.0
        )
        assert score == 80.0
        assert weights["semantic_weight"] == 0.40
        assert weights["required_skill_weight"] == 0.40
        assert weights["preferred_skill_weight"] == 0.20

    def test_overall_score_renormalization_without_preferred_skills(self):
        # When preferred is None, semantic (0.40) and req (0.40) renormalize to 50% and 50%
        # 50% of 70 + 50% of 90 = 35 + 45 = 80.0
        score, weights = self.engine.calculate_overall_score(
            semantic_score=70.0,
            required_coverage=90.0,
            preferred_coverage=None
        )
        assert score == 80.0
        assert weights["semantic_weight"] == 0.50
        assert weights["required_skill_weight"] == 0.50
        assert weights["preferred_skill_weight"] == 0.0

    def test_score_clamping(self):
        # Clamps out of bound numbers to 0-100
        score_high, _ = self.engine.calculate_overall_score(150.0, 120.0, 110.0)
        assert score_high == 100.0

        score_low, _ = self.engine.calculate_overall_score(-20.0, -10.0, None)
        assert score_low == 0.0

    def test_tfidf_fallback(self):
        resume = "Senior Python developer experienced in FastAPI, PostgreSQL, and cloud microservices."
        jd = "Looking for a Python developer with FastAPI and PostgreSQL background."
        score = self.engine.compute_tfidf_fallback(resume, jd)
        assert 0.0 <= score <= 100.0
        assert score > 30.0  # Common words should yield positive similarity

    def test_text_preprocessor_overlapping_chunks(self):
        long_text = "word " * 300
        chunks = self.preprocessor.create_overlapping_chunks(long_text)
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk.split()) <= 120
