import json
from pathlib import Path
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.agents.final_resume_quality_agent import run as quality_check
from app.agents.ats_agent import _fallback_analyze as analyze_ats_format
from app.agents.resume_formatting_agent import run as format_resume
from app.agents.resume_optimization_agent import run as optimize_resume
from app.agents.resume_validation_agent import run as validate_resume
from app.api.deps import get_current_user
from app.database.connection import get_db
from app.models.analysis import Analysis
from app.models.generated_resume import GeneratedResume
from app.models.resume import Resume
from app.models.user import User
from app.services.resume_document_service import generate_resume_documents
from app.services.scoring_service import score_analysis

router = APIRouter(prefix="/api", tags=["Generated Resume"])


class TemplateRequest(BaseModel):
    template_name: Literal["ATS Professional", "Modern Professional", "Minimal"]


def _storage_root() -> Path:
    return Path(__file__).resolve().parents[2] / "generated_resumes"


def _get_user_resume(db: Session, user_id: int, resume_id: int) -> Resume:
    resume = db.query(Resume).filter(Resume.id == resume_id, Resume.user_id == user_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")
    return resume


def _get_user_analysis(db: Session, user_id: int, analysis_id: int) -> Analysis:
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id, Analysis.user_id == user_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    return analysis


def _build_optimized_document(analysis: Analysis, resume: Resume) -> dict:
    jd = analysis.job_description
    if not jd:
        raise HTTPException(status_code=404, detail="Job description not found.")

    matching_skills = [skill.skill_name for skill in analysis.extracted_skills if skill.present_in_resume]
    missing_skills = [
        skill.skill_name
        for skill in analysis.extracted_skills
        if skill.required_by_job and not skill.present_in_resume
    ]
    recommendations = [
        {
            "category": item.category,
            "recommendation": item.recommendation,
            "priority": item.priority,
        }
        for item in analysis.recommendations
    ]

    optimized = optimize_resume(
        resume.extracted_text,
        jd.description,
        {
            "matching_skills": matching_skills,
            "missing_skills": missing_skills,
            "missing_keywords": [item.keyword for item in analysis.missing_keywords],
            "recommendations": recommendations,
            "ats_issues": [],
        },
        recommendations,
    )
    validation = validate_resume(resume.extracted_text, optimized)
    if not validation["is_valid"]:
        raise HTTPException(
            status_code=422,
            detail="Resume optimization was blocked because the generated content could not be verified against the original resume.",
        )
    formatting = format_resume(optimized)
    quality = quality_check(optimized["optimized_text"], optimized)

    return {
        "optimized": optimized,
        "validation": validation,
        "formatting": formatting,
        "quality": quality,
    }


def _score_resume_text(text: str, analysis: Analysis) -> dict:
    return score_analysis({
        "ats_score": analyze_ats_format(text)["ats_score"],
        "skill_score": analysis.skill_score,
        "keyword_score": analysis.keyword_score,
        "experience_score": analysis.experience_score,
        "education_score": analysis.education_score,
        "resume_quality_score": analysis.resume_quality_score,
    })


@router.post("/resumes/{resume_id}/optimize", status_code=201)
def optimize_resume_endpoint(
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    resume = _get_user_resume(db, current_user.id, resume_id)
    analysis = (
        db.query(Analysis)
        .filter(Analysis.resume_id == resume.id, Analysis.user_id == current_user.id)
        .order_by(Analysis.created_at.desc())
        .first()
    )
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found for this resume.")

    payload = _build_optimized_document(analysis, resume)
    optimized_text = payload["optimized"]["optimized_text"]
    original_scores = _score_resume_text(resume.extracted_text, analysis)
    optimized_scores = _score_resume_text(optimized_text, analysis)

    doc_root = _storage_root() / f"user_{current_user.id}" / f"analysis_{analysis.id}"
    doc_root.mkdir(parents=True, exist_ok=True)
    version = uuid4().hex
    pdf_path, docx_path = generate_resume_documents(optimized_text, str(doc_root), f"resume_{version}")

    record = GeneratedResume(
        user_id=current_user.id,
        analysis_id=analysis.id,
        original_resume_id=resume.id,
        template_name="ATS Professional",
        optimized_content_json=json.dumps(payload),
        optimized_text=optimized_text,
        original_ats_score=analyze_ats_format(resume.extracted_text)["ats_score"],
        optimized_ats_score=analyze_ats_format(optimized_text)["ats_score"],
        original_job_match_score=original_scores["job_match_score"],
        optimized_job_match_score=optimized_scores["job_match_score"],
        original_overall_score=original_scores["overall_score"],
        optimized_overall_score=optimized_scores["overall_score"],
        pdf_file_path=pdf_path,
        docx_file_path=docx_path,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return {"generated_resume_id": record.id, "message": "Resume optimization completed.", "template": record.template_name}


@router.post("/analyses/{analysis_id}/generate-resume")
def generate_resume_from_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    analysis = _get_user_analysis(db, current_user.id, analysis_id)
    resume = analysis.resume
    if resume is None:
        raise HTTPException(status_code=404, detail="Original resume not found.")

    payload = _build_optimized_document(analysis, resume)
    optimized_text = payload["optimized"]["optimized_text"]
    original_scores = _score_resume_text(resume.extracted_text, analysis)
    optimized_scores = _score_resume_text(optimized_text, analysis)

    doc_root = _storage_root() / f"user_{current_user.id}" / f"analysis_{analysis.id}"
    doc_root.mkdir(parents=True, exist_ok=True)
    version = uuid4().hex
    pdf_path, docx_path = generate_resume_documents(optimized_text, str(doc_root), f"resume_{version}")

    record = GeneratedResume(
        user_id=current_user.id,
        analysis_id=analysis.id,
        original_resume_id=resume.id,
        template_name="ATS Professional",
        optimized_content_json=json.dumps({
            "validation": payload["validation"],
            "formatting": payload["formatting"],
            "quality": payload["quality"],
            "optimized_text": optimized_text,
        }),
        optimized_text=optimized_text,
        original_ats_score=analyze_ats_format(resume.extracted_text)["ats_score"],
        optimized_ats_score=analyze_ats_format(optimized_text)["ats_score"],
        original_job_match_score=original_scores["job_match_score"],
        optimized_job_match_score=optimized_scores["job_match_score"],
        original_overall_score=original_scores["overall_score"],
        optimized_overall_score=optimized_scores["overall_score"],
        pdf_file_path=pdf_path,
        docx_file_path=docx_path,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return {"generated_resume_id": record.id, "status": "generated"}


@router.get("/generated-resumes/{id}")
def get_generated_resume(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    record = db.query(GeneratedResume).filter(GeneratedResume.id == id, GeneratedResume.user_id == current_user.id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Generated resume not found.")
    return {
        "id": record.id,
        "analysis_id": record.analysis_id,
        "template_name": record.template_name,
        "optimized_text": record.optimized_text,
        "original_ats_score": record.original_ats_score,
        "optimized_ats_score": record.optimized_ats_score,
        "original_job_match_score": record.original_job_match_score,
        "optimized_job_match_score": record.optimized_job_match_score,
        "original_overall_score": record.original_overall_score,
        "optimized_overall_score": record.optimized_overall_score,
        "created_at": record.created_at,
    }


@router.put("/generated-resumes/{id}/template")
def update_generated_resume_template(
    id: int,
    request: TemplateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = db.query(GeneratedResume).filter(
        GeneratedResume.id == id,
        GeneratedResume.user_id == current_user.id,
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Generated resume not found.")

    output_dir = Path(record.pdf_file_path).parent if record.pdf_file_path else _storage_root() / f"user_{current_user.id}" / f"analysis_{record.analysis_id}"
    version = uuid4().hex
    pdf_path, docx_path = generate_resume_documents(
        record.optimized_text,
        str(output_dir),
        f"resume_{version}",
        request.template_name,
    )
    record.template_name = request.template_name
    record.pdf_file_path = pdf_path
    record.docx_file_path = docx_path
    db.commit()
    return {"template_name": record.template_name}


@router.get("/generated-resumes/{id}/preview")
def preview_generated_resume(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    record = db.query(GeneratedResume).filter(GeneratedResume.id == id, GeneratedResume.user_id == current_user.id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Generated resume not found.")
    return {"preview": record.optimized_text}


@router.get("/generated-resumes/{id}/download/pdf")
def download_generated_resume_pdf(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    record = db.query(GeneratedResume).filter(GeneratedResume.id == id, GeneratedResume.user_id == current_user.id).first()
    if not record or not record.pdf_file_path:
        raise HTTPException(status_code=404, detail="PDF not available.")
    path = Path(record.pdf_file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="PDF file is missing.")
    return FileResponse(path, media_type="application/pdf", filename=f"optimized_resume_{id}.pdf")


@router.get("/generated-resumes/{id}/download/docx")
def download_generated_resume_docx(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    record = db.query(GeneratedResume).filter(GeneratedResume.id == id, GeneratedResume.user_id == current_user.id).first()
    if not record or not record.docx_file_path:
        raise HTTPException(status_code=404, detail="DOCX not available.")
    path = Path(record.docx_file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="DOCX file is missing.")
    return FileResponse(path, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", filename=f"optimized_resume_{id}.docx")


@router.post("/generated-resumes/{id}/reanalyze")
def reanalyze_generated_resume(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    record = db.query(GeneratedResume).filter(GeneratedResume.id == id, GeneratedResume.user_id == current_user.id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Generated resume not found.")

    analysis = _get_user_analysis(db, current_user.id, record.analysis_id)
    optimized_scores = _score_resume_text(record.optimized_text, analysis)
    record.optimized_ats_score = analyze_ats_format(record.optimized_text)["ats_score"]
    record.optimized_job_match_score = optimized_scores["job_match_score"]
    record.optimized_overall_score = optimized_scores["overall_score"]
    db.commit()
    return {"message": "Resume reanalyzed.", "scores": optimized_scores}
