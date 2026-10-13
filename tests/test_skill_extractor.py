import pytest
from backend.services.skill_extractor import SkillExtractor


class TestSkillExtractor:
    def setup_method(self):
        self.extractor = SkillExtractor()

    def test_alias_detection(self):
        text = "Experienced in sklearn, postgres, k8s, and writing rest apis."
        skills = self.extractor.extract_skills(text)
        
        assert "Scikit-Learn" in skills
        assert "PostgreSQL" in skills
        assert "Kubernetes" in skills
        assert "REST APIs" in skills

    def test_avoid_false_positive_for_short_names(self):
        # Words like 'Can', 'Care', 'Good', 'Run', 'Cat' should NOT trigger 'C', 'Go', 'R'
        text = "I can care for cats and run a good campaign."
        skills = self.extractor.extract_skills(text)
        
        assert "C" not in skills
        assert "R" not in skills
        assert "Go (Golang)" not in skills

    def test_legitimate_short_name_matches(self):
        # Strict pattern should match when in programming list context
        text_c = "Strong knowledge of C / C++ and embedded systems."
        skills_c = self.extractor.extract_skills(text_c)
        assert "C" in skills_c
        assert "C++" in skills_c

        text_go = "Engineered microservices using Golang and Docker."
        skills_go = self.extractor.extract_skills(text_go)
        assert "Go (Golang)" in skills_go
        assert "Docker" in skills_go

    def test_job_description_splitting(self):
        jd = (
            "About the job:\n"
            "Required Qualifications:\n"
            "- Python, FastAPI, PostgreSQL\n\n"
            "Preferred Qualifications:\n"
            "- AWS, Kubernetes, React"
        )
        req_part, pref_part = self.extractor.split_job_description_requirements(jd)
        assert "FastAPI" in req_part
        assert "Kubernetes" in pref_part

    def test_compare_skills_grouping_and_coverage(self):
        resume = "Skills: Python, FastAPI, Docker, Git, Redis."
        jd = (
            "Required Qualifications:\n"
            "- Python, FastAPI, PostgreSQL\n\n"
            "Preferred Qualifications:\n"
            "- Docker, AWS"
        )
        matching, missing, additional, stats = self.extractor.compare_skills(resume, jd)
        
        match_names = [s.name for s in matching]
        missing_names = [s.name for s in missing]
        add_names = [s.name for s in additional]

        assert "Python" in match_names
        assert "FastAPI" in match_names
        assert "Docker" in match_names

        assert "PostgreSQL" in missing_names
        assert "AWS" in missing_names

        assert "Redis" in add_names or "Git" in add_names

        # Python & FastAPI matched out of [Python, FastAPI, PostgreSQL] -> 2/3 = 66.67%
        assert 66.0 <= stats["required_coverage"] <= 67.0
        # Docker matched out of [Docker, AWS] -> 1/2 = 50.0%
        assert stats["preferred_coverage"] == 50.0
