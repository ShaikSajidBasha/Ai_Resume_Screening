"""
Runs the full multi-agent analysis pipeline and exposes history endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.resume import Resume
from app.models.job_description import JobDescription
from app.models.analysis import Analysis
from app.schemas.analysis import AnalyzeRequest, AnalysisResultOut, AnalysisHistoryItem
from app.services.analysis_service import run_full_analysis
from app.services.google_ai_service import AIServiceError

router = APIRouter(prefix="/api/analyses", tags=["Analysis"])


def _build_result_out(analysis: Analysis) -> AnalysisResultOut:
    runtime = getattr(analysis, "_runtime", {})
    return AnalysisResultOut(
        analysis_id=analysis.id,
        scores={
            "ats_score": analysis.ats_score,
            "job_match_score": analysis.job_match_score,
            "skill_score": analysis.skill_score,
            "keyword_score": analysis.keyword_score,
            "experience_score": analysis.experience_score,
            "education_score": analysis.education_score,
            "resume_quality_score": analysis.resume_quality_score,
            "overall_score": analysis.overall_score,
        },
        weights={
            "ats_score": 0.25, "skill_score": 0.30, "keyword_score": 0.15,
            "experience_score": 0.15, "education_score": 0.10, "resume_quality_score": 0.05,
        },
        matching_skills=runtime.get("matching_skills", []),
        missing_skills=runtime.get("missing_skills", []),
        matching_keywords=runtime.get("matching_keywords", []),
        missing_keywords=runtime.get("missing_keywords_detail", []),
        ats_issues=runtime.get("ats_issues", []),
        strengths=runtime.get("strengths", []),
        weaknesses=runtime.get("weaknesses", []),
        recommendations=runtime.get("recommendations", []),
        final_summary=analysis.recommendation or runtime.get("final_summary", ""),
        status=analysis.status or "",
    )


@router.post("", response_model=AnalysisResultOut, status_code=status.HTTP_201_CREATED)
def analyze(
    payload: AnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    resume = db.query(Resume).filter(Resume.id == payload.resume_id, Resume.user_id == current_user.id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")

    jd = db.query(JobDescription).filter(
        JobDescription.id == payload.job_description_id, JobDescription.user_id == current_user.id
    ).first()
    if not jd:
        raise HTTPException(status_code=404, detail="Job description not found.")

    try:
        analysis = run_full_analysis(db, current_user.id, resume, jd)
    except AIServiceError as exc:
        raise HTTPException(status_code=503, detail="AI analysis is temporarily unavailable. Please try again.") from exc
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        raise HTTPException(status_code=500, detail="Unable to save analysis. Please try again.") from exc

    return _build_result_out(analysis)


@router.get("", response_model=list[AnalysisHistoryItem])
def list_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = (
        db.query(Analysis)
        .filter(Analysis.user_id == current_user.id)
        .order_by(Analysis.created_at.desc())
        .all()
    )
    items = []
    for a in rows:
        items.append(AnalysisHistoryItem(
            id=a.id,
            resume_file_name=a.resume.file_name if a.resume else "",
            job_title=a.job_description.title if a.job_description else "",
            ats_score=a.ats_score,
            job_match_score=a.job_match_score,
            overall_score=a.overall_score,
            status=a.status,
            created_at=a.created_at,
        ))
    return items


@router.get("/{analysis_id}", response_model=AnalysisResultOut)
def get_analysis(analysis_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id, Analysis.user_id == current_user.id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found.")

    matching_skills = [s.skill_name for s in analysis.extracted_skills if s.present_in_resume and s.required_by_job]
    missing_skills = [s.skill_name for s in analysis.extracted_skills if s.required_by_job and not s.present_in_resume]
    missing_kw = [{"keyword": k.keyword, "status": "Missing", "importance": k.importance} for k in analysis.missing_keywords]
    recs = [{"category": r.category, "recommendation": r.recommendation, "priority": r.priority} for r in analysis.recommendations]

    analysis._runtime = {
        "matching_skills": matching_skills,
        "missing_skills": missing_skills,
        "matching_keywords": [],
        "missing_keywords_detail": missing_kw,
        "ats_issues": [],
        "strengths": [],
        "weaknesses": [],
        "recommendations": recs,
        "final_summary": analysis.recommendation or "",
    }
    return _build_result_out(analysis)


@router.delete("/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_analysis(analysis_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id, Analysis.user_id == current_user.id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    db.delete(analysis)
    db.commit()
    return None
