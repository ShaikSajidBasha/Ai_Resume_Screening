from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class AnalyzeRequest(BaseModel):
    resume_id: int
    job_description_id: int


class ScoreBreakdown(BaseModel):
    ats_score: float
    job_match_score: float
    skill_score: float
    keyword_score: float
    experience_score: float
    education_score: float
    resume_quality_score: float
    overall_score: float


class AnalysisResultOut(BaseModel):
    analysis_id: int
    scores: ScoreBreakdown
    weights: dict
    matching_skills: List[str]
    missing_skills: List[str]
    matching_keywords: List[str]
    missing_keywords: List[dict]
    ats_issues: List[str]
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[dict]
    final_summary: str
    status: str
    disclaimer: str = (
        "AI-generated scores are estimates for resume optimization and should not be "
        "treated as a final hiring decision."
    )


class AnalysisHistoryItem(BaseModel):
    id: int
    resume_file_name: str
    job_title: str
    ats_score: float
    job_match_score: float
    overall_score: float
    status: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
