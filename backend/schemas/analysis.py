from typing import List, Optional, Dict
from pydantic import BaseModel, Field

class SkillItem(BaseModel):
    name: str = Field(..., description="Canonical name of the skill")
    category: str = Field(..., description="Skill taxonomy category (e.g. Programming, Cloud, AI/ML)")
    is_required: bool = Field(default=True, description="True if required by job description, False if preferred")
    evidence_snippet: Optional[str] = Field(default=None, description="Excerpt where the skill was found")
    section_found: Optional[str] = Field(default=None, description="Resume section where skill was detected")

class ScoresBreakdown(BaseModel):
    overall_score: float = Field(..., ge=0.0, le=100.0, description="Weighted composite alignment score (0-100)")
    semantic_score: float = Field(..., ge=0.0, le=100.0, description="Embedding cosine similarity score (0-100)")
    required_skill_score: float = Field(..., ge=0.0, le=100.0, description="Required skill coverage percentage (0-100)")
    preferred_skill_score: Optional[float] = Field(default=None, ge=0.0, le=100.0, description="Preferred skill coverage percentage (0-100) or None if absent")
    weights_applied: Dict[str, float] = Field(..., description="Normalized weights used to compute overall score")
    disclaimer: str = Field(
        default="Scores represent textual alignment between the submitted resume and job description. They do not constitute hiring probabilities or automated employment decisions.",
        description="Standard transparency disclaimer"
    )

class RecommendationItem(BaseModel):
    issue: str = Field(..., description="Gap or area of improvement identified")
    why_it_matters: str = Field(..., description="Context on why this requirement is critical for the target role")
    recommended_action: str = Field(..., description="Actionable suggestion for the candidate")
    example_rewrite: Optional[str] = Field(default=None, description="Truthful illustrative rewrite based strictly on candidate's context")
    user_verification_notice: str = Field(
        default="Please review all suggested text for 100% accuracy and truthfulness before adopting.",
        description="Verification instruction"
    )

class ExperienceAnalysis(BaseModel):
    sections_detected: List[str] = Field(default_factory=list, description="Sections discovered in resume")
    observations: List[str] = Field(default_factory=list, description="Findings regarding experience and requirements")
    education_detected: List[str] = Field(default_factory=list, description="Education items identified")
    experience_years_comparison: Optional[str] = Field(default=None, description="Years of experience alignment note")

class AnalysisResponse(BaseModel):
    target_job_title: Optional[str] = Field(default=None, description="Target job title evaluated")
    scores: ScoresBreakdown = Field(..., description="Explainable scoring metrics")
    matching_skills: List[SkillItem] = Field(default_factory=list, description="Skills present in both resume and JD")
    missing_skills: List[SkillItem] = Field(default_factory=list, description="Skills mentioned in JD but absent/unsubstantiated in resume")
    additional_skills: List[SkillItem] = Field(default_factory=list, description="Strong technical skills in resume not explicitly in JD")
    experience_analysis: ExperienceAnalysis = Field(..., description="Experience and qualifications breakdown")
    recommendations: List[RecommendationItem] = Field(default_factory=list, description="Actionable resume enhancement advice")
    resume_word_count: int = Field(..., description="Word count of parsed resume text")
    jd_word_count: int = Field(..., description="Word count of parsed job description")
    processing_time_seconds: float = Field(..., description="Time taken to process the analysis in seconds")

class HealthResponse(BaseModel):
    status: str = Field(..., description="Service status ('healthy' or 'degraded')")
    model_loaded: bool = Field(..., description="Whether embedding model is loaded into memory")
    model_name: str = Field(..., description="Loaded embedding model identifier")
    supported_formats: List[str] = Field(..., description="File formats supported for upload")

class ResumeExtractResponse(BaseModel):
    filename: str
    file_type: str
    character_count: int
    word_count: int
    sections_detected: List[str]
    preview_snippet: str
