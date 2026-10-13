import pytest
from backend.services.recommendation_engine import RecommendationEngine
from backend.schemas.analysis import SkillItem


class TestRecommendationEngine:
    def setup_method(self):
        self.engine = RecommendationEngine()

    def test_experience_and_degree_analysis(self):
        resume = (
            "Jane Doe\n"
            "Summary: Professional engineer with 6 years experience.\n"
            "Education: Bachelor of Science in Computer Science.\n"
            "Experience: Built 10+ microservices serving 100k users."
        )
        jd = "Seeking Senior Engineer with 5+ years of experience and a Bachelor's Degree in Computer Science."
        
        analysis = self.engine.analyze_experience_and_qualifications(
            resume_text=resume,
            jd_text=jd,
            detected_sections=["Summary", "Education", "Experience"]
        )
        
        assert "Bachelor's Degree or Equivalent" in analysis.education_detected
        assert "6" in str(analysis.experience_years_comparison)
        assert len(analysis.observations) > 0

    def test_recommendations_for_missing_required_skills(self):
        missing = [
            SkillItem(name="Kubernetes", category="DevOps", is_required=True, evidence_snippet="Must have K8s"),
            SkillItem(name="Docker", category="DevOps", is_required=True, evidence_snippet="Docker required"),
        ]
        recs = self.engine.generate_recommendations(
            matching_skills=[],
            missing_skills=missing,
            additional_skills=[],
            resume_text="Experienced Python developer.",
            target_job_title="DevOps Engineer"
        )
        
        assert len(recs) >= 1
        top_rec = recs[0]
        assert "Kubernetes" in top_rec.issue
        assert "DevOps Engineer" in top_rec.why_it_matters or "target role" in top_rec.why_it_matters
        assert top_rec.example_rewrite is not None
        assert "accuracy" in top_rec.user_verification_notice.lower()

    def test_passive_bullet_detection(self):
        resume_with_passive = (
            "Experience:\n"
            "- Responsible for maintaining database servers.\n"
            "- Helped with writing API endpoints."
        )
        recs = self.engine.generate_recommendations(
            matching_skills=[],
            missing_skills=[],
            additional_skills=[],
            resume_text=resume_with_passive
        )
        
        passive_recs = [r for r in recs if "passive" in r.issue.lower()]
        assert len(passive_recs) == 1
        assert "Action" in passive_recs[0].recommended_action or "verb" in passive_recs[0].recommended_action.lower()
