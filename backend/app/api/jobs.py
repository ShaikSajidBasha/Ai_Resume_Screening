"""
Job Description CRUD (create + list) endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.job_description import JobDescription
from app.schemas.job import JobDescriptionCreate, JobDescriptionOut
from app.utils.validators import validate_job_description, FileValidationError

router = APIRouter(prefix="/api/job-descriptions", tags=["Job Description"])


@router.post("", response_model=JobDescriptionOut, status_code=status.HTTP_201_CREATED)
def create_job_description(
    payload: JobDescriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        validate_job_description(payload.description)
    except FileValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    jd = JobDescription(
        user_id=current_user.id,
        title=payload.title,
        company=payload.company,
        description=payload.description,
    )
    db.add(jd)
    db.commit()
    db.refresh(jd)
    return jd


@router.get("", response_model=list[JobDescriptionOut])
def list_job_descriptions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return (
        db.query(JobDescription)
        .filter(JobDescription.user_id == current_user.id)
        .order_by(JobDescription.created_at.desc())
        .all()
    )
