"""
Aggregated stats for the dashboard: totals, averages, recent items.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.analysis import Analysis
from app.models.resume import Resume
from app.models.job_description import JobDescription

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("")
def get_dashboard(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = db.query(Analysis).filter(Analysis.user_id == current_user.id)
    total_analyses = q.count()

    avg_ats = db.query(func.avg(Analysis.ats_score)).filter(Analysis.user_id == current_user.id).scalar() or 0
    avg_match = db.query(func.avg(Analysis.job_match_score)).filter(Analysis.user_id == current_user.id).scalar() or 0
    avg_overall = db.query(func.avg(Analysis.overall_score)).filter(Analysis.user_id == current_user.id).scalar() or 0

    latest = q.order_by(Analysis.created_at.desc()).first()
    recent_analyses = q.order_by(Analysis.created_at.desc()).limit(5).all()
    recent_resumes = (
        db.query(Resume).filter(Resume.user_id == current_user.id).order_by(Resume.uploaded_at.desc()).limit(5).all()
    )
    recent_jobs = (
        db.query(JobDescription)
        .filter(JobDescription.user_id == current_user.id)
        .order_by(JobDescription.created_at.desc())
        .limit(5)
        .all()
    )

    return {
        "total_analyses": total_analyses,
        "average_ats_score": round(float(avg_ats), 2),
        "average_job_match_score": round(float(avg_match), 2),
        "average_overall_score": round(float(avg_overall), 2),
        "latest_analysis": {
            "id": latest.id,
            "overall_score": latest.overall_score,
            "status": latest.status,
            "created_at": latest.created_at.isoformat(),
        } if latest else None,
        "score_trend": [
            {"date": a.created_at.strftime("%Y-%m-%d"), "ats_score": a.ats_score,
             "job_match_score": a.job_match_score, "overall_score": a.overall_score}
            for a in reversed(recent_analyses)
        ],
        "recent_resumes": [{"id": r.id, "file_name": r.file_name, "uploaded_at": r.uploaded_at.isoformat()} for r in recent_resumes],
        "recent_job_descriptions": [{"id": j.id, "title": j.title, "company": j.company} for j in recent_jobs],
    }
