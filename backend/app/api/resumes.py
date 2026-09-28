"""
Resume upload endpoint: validates + extracts text + persists to MySQL.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.resume import Resume
from app.schemas.resume import ResumeOut
from app.services.resume_service import extract_resume_text, ResumeProcessingError

router = APIRouter(prefix="/api/resumes", tags=["Resume"])


@router.post("/upload", response_model=ResumeOut, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    file_bytes = await file.read()

    try:
        text, ext = extract_resume_text(file, file_bytes)
    except ResumeProcessingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    resume = Resume(
        user_id=current_user.id,
        file_name=file.filename,
        file_type=ext.replace(".", ""),
        extracted_text=text,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


@router.get("", response_model=list[ResumeOut])
def list_resumes(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return (
        db.query(Resume)
        .filter(Resume.user_id == current_user.id)
        .order_by(Resume.uploaded_at.desc())
        .all()
    )
