import time
from typing import Optional
from fastapi import APIRouter, File, Form, UploadFile, HTTPException, status
from ..config import settings
from ..schemas.analysis import (
    AnalysisResponse,
    ResumeExtractResponse,
    ScoresBreakdown
)
from ..services.resume_parser import ResumeParser, ResumeParsingError
from ..services.skill_extractor import SkillExtractor
from ..services.similarity_engine import SimilarityEngine
from ..services.recommendation_engine import RecommendationEngine

router = APIRouter(prefix="", tags=["Analysis"])

# Service instances
resume_parser = ResumeParser(
    max_size_mb=settings.max_upload_size_mb,
    min_chars=settings.min_extracted_text_chars
)
skill_extractor = SkillExtractor()
similarity_engine = SimilarityEngine(
    model_name=settings.embedding_model_name,
    semantic_weight=settings.semantic_weight,
    required_skill_weight=settings.required_skill_weight,
    preferred_skill_weight=settings.preferred_skill_weight
)
recommendation_engine = RecommendationEngine()


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    summary="Analyze Resume against Job Description",
    description="Upload a PDF or DOCX resume along with a job description to calculate semantic similarity, skill gaps, and personalized recommendations."
)
async def analyze_resume_endpoint(
    resume: UploadFile = File(..., description="Resume file (.pdf or .docx)"),
    job_description: str = Form(..., description="Full text of the target job description"),
    target_job_title: Optional[str] = Form(None, description="Optional target job title")
):
    start_time = time.time()

    # 1. Input validations
    if not job_description or len(job_description.strip()) < 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job description is too short. Please paste a comprehensive job description with at least 20 characters."
        )

    # 2. Read resume file bytes safely in memory
    try:
        file_bytes = await resume.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not read uploaded file: {str(e)}"
        )
    finally:
        await resume.close()

    # 3. Parse and extract resume text
    try:
        resume_text, detected_sections = resume_parser.parse_file(resume.filename or "resume", file_bytes)
    except ResumeParsingError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error while processing resume file: {str(e)}"
        )

    clean_jd = job_description.strip()

    # 4. Extract and compare skills
    matching_skills, missing_skills, additional_skills, coverage_stats = skill_extractor.compare_skills(
        resume_text=resume_text,
        jd_text=clean_jd
    )

    # 5. Compute semantic similarity and overall weighted score
    semantic_score = round(
        similarity_engine.compute_semantic_similarity(
            resume_text=resume_text,
            jd_text=clean_jd
        ),
        2
    )

    overall_score, weights_applied = similarity_engine.calculate_overall_score(
        semantic_score=semantic_score,
        required_coverage=coverage_stats["required_coverage"],
        preferred_coverage=coverage_stats["preferred_coverage"]
    )

    scores_breakdown = ScoresBreakdown(
        overall_score=overall_score,
        semantic_score=semantic_score,
        required_skill_score=coverage_stats["required_coverage"],
        preferred_skill_score=coverage_stats["preferred_coverage"],
        weights_applied=weights_applied
    )

    # 6. Analyze experience & qualifications
    experience_analysis = recommendation_engine.analyze_experience_and_qualifications(
        resume_text=resume_text,
        jd_text=clean_jd,
        detected_sections=detected_sections
    )

    # 7. Generate actionable recommendations
    recommendations = recommendation_engine.generate_recommendations(
        matching_skills=matching_skills,
        missing_skills=missing_skills,
        additional_skills=additional_skills,
        resume_text=resume_text,
        target_job_title=target_job_title
    )

    duration = time.time() - start_time

    return AnalysisResponse(
        target_job_title=target_job_title.strip() if target_job_title else None,
        scores=scores_breakdown,
        matching_skills=matching_skills,
        missing_skills=missing_skills,
        additional_skills=additional_skills,
        experience_analysis=experience_analysis,
        recommendations=recommendations,
        resume_word_count=len(resume_text.split()),
        jd_word_count=len(clean_jd.split()),
        processing_time_seconds=round(duration, 2)
    )


@router.post(
    "/extract-resume",
    response_model=ResumeExtractResponse,
    summary="Extract & Validate Resume Text",
    description="Validates and extracts metadata from an uploaded resume without storing contents or logging personal data."
)
async def extract_resume_endpoint(
    resume: UploadFile = File(..., description="Resume file (.pdf or .docx)")
):
    try:
        file_bytes = await resume.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not read uploaded file: {str(e)}"
        )
    finally:
        await resume.close()

    try:
        resume_text, detected_sections = resume_parser.parse_file(resume.filename or "resume", file_bytes)
    except ResumeParsingError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )

    preview = resume_text[:200] + ("..." if len(resume_text) > 200 else "")
    file_type = "PDF" if (resume.filename or "").lower().endswith(".pdf") else "DOCX"

    return ResumeExtractResponse(
        filename=resume.filename or "uploaded_file",
        file_type=file_type,
        character_count=len(resume_text),
        word_count=len(resume_text.split()),
        sections_detected=detected_sections,
        preview_snippet=preview
    )
