import io
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from tests.test_resume_parser import create_synthetic_pdf, create_synthetic_docx
from backend.services.report_generator import ReportGenerator
from backend.schemas.analysis import AnalysisResponse

client = TestClient(app)


class TestAPIEndpoints:
    def test_root_endpoint(self):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "online"
        assert "AI Resume" in data["app_name"]

    def test_health_endpoint(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        assert "supported_formats" in data

    def test_analyze_endpoint_with_valid_pdf(self):
        resume_content = (
            "Alex Mercer\n"
            "Summary: Full Stack Engineer with 4 years experience in Python and FastAPI.\n"
            "Skills: Python, FastAPI, Docker, PostgreSQL, React, Git.\n"
            "Experience: Built scalable microservices and REST APIs."
        )
        pdf_bytes = create_synthetic_pdf(resume_content)
        jd_text = (
            "Required Qualifications:\n"
            "- 3+ years experience with Python and FastAPI.\n"
            "- Knowledge of PostgreSQL and Docker.\n"
            "Preferred Qualifications:\n"
            "- Experience with React and AWS."
        )

        response = client.post(
            "/analyze",
            files={"resume": ("alex_resume.pdf", pdf_bytes, "application/pdf")},
            data={
                "job_description": jd_text,
                "target_job_title": "Backend Python Engineer"
            }
        )

        assert response.status_code == 200
        result = response.json()
        assert result["target_job_title"] == "Backend Python Engineer"
        
        # Verify scores structure
        scores = result["scores"]
        assert 0.0 <= scores["overall_score"] <= 100.0
        assert 0.0 <= scores["semantic_score"] <= 100.0
        assert 0.0 <= scores["required_skill_score"] <= 100.0
        assert scores["preferred_skill_score"] is not None

        # Verify skills
        matching_names = [s["name"] for s in result["matching_skills"]]
        assert "Python" in matching_names
        assert "FastAPI" in matching_names

        # Verify recommendations
        assert len(result["recommendations"]) > 0

    def test_analyze_endpoint_with_valid_docx(self):
        paragraphs = [
            "Taylor Swift",
            "Summary: AI and Data Scientist with deep learning experience.",
            "Skills: Python, PyTorch, Pandas, NumPy, Scikit-Learn, SQL.",
            "Experience: Developed predictive deep neural network pipelines."
        ]
        docx_bytes = create_synthetic_docx(paragraphs)
        jd_text = (
            "We are seeking an AI Engineer with PyTorch, Python, and Scikit-Learn experience. "
            "Bachelor's degree in CS required."
        )

        response = client.post(
            "/analyze",
            files={"resume": ("taylor_resume.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            data={"job_description": jd_text}
        )

        assert response.status_code == 200
        result = response.json()
        matching_names = [s["name"] for s in result["matching_skills"]]
        assert "PyTorch" in matching_names or "Python" in matching_names

    def test_analyze_short_job_description_validation(self):
        pdf_bytes = create_synthetic_pdf("Some valid resume text")
        response = client.post(
            "/analyze",
            files={"resume": ("test.pdf", pdf_bytes, "application/pdf")},
            data={"job_description": "Too short"}
        )
        assert response.status_code == 400
        assert "too short" in response.json()["detail"].lower()

    def test_analyze_unsupported_file_format(self):
        response = client.post(
            "/analyze",
            files={"resume": ("test.txt", b"Unsupported content", "text/plain")},
            data={"job_description": "A comprehensive job description for software engineers."}
        )
        assert response.status_code == 400
        assert "unsupported" in response.json()["detail"].lower()

    def test_extract_resume_endpoint(self):
        resume_content = (
            "Morgan Freeman\n"
            "Summary: Senior Developer.\n"
            "Skills: Python, AWS, Docker.\n"
            "Experience: 10 years building cloud applications."
        )
        pdf_bytes = create_synthetic_pdf(resume_content)

        response = client.post(
            "/extract-resume",
            files={"resume": ("morgan.pdf", pdf_bytes, "application/pdf")}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "morgan.pdf"
        assert data["file_type"] == "PDF"
        assert data["word_count"] > 5
        assert "Summary" in data["sections_detected"] or "Skills" in data["sections_detected"]

    def test_report_generator_markdown_and_json(self):
        resume_content = "Skills: Python, FastAPI. Experience: 3 years building scalable cloud microservices."
        pdf_bytes = create_synthetic_pdf(resume_content)
        jd_text = "Looking for Python, FastAPI, and Docker skills with at least 2 years experience."

        response = client.post(
            "/analyze",
            files={"resume": ("test.pdf", pdf_bytes, "application/pdf")},
            data={"job_description": jd_text}
        )
        assert response.status_code == 200
        analysis_data = AnalysisResponse(**response.json())

        # Test Markdown Report
        md = ReportGenerator.generate_markdown_report(analysis_data)
        assert "# AI Resume & Job Description Match Report" in md
        assert "Overall Alignment Score" in md
        assert "Disclaimer" in md

        # Test JSON Report
        json_rep = ReportGenerator.generate_json_report(analysis_data)
        assert "overall_score" in json_rep
