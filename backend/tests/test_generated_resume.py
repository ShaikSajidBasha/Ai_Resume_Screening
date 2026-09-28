from app.api import generated_resumes
from app.api.deps import get_current_user
from app.models.analysis import Analysis
from app.models.job_description import JobDescription
from app.models.resume import Resume
from app.models.user import User


def test_generate_resume_preserves_source_and_supports_downloads(client, db_session, monkeypatch, tmp_path):
    original_text = """Alex Smith
alex.smith@example.com
+1 555 123 4567

Skills
Python, SQL

Education
Bachelor of Science in Computing

Experience
Data Analyst at Acme Labs
Analyzed sales data using Python and SQL.

Projects
Sales dashboard built with Python.
"""
    user = User(name="Alex Smith", email="alex@example.com", password_hash="test")
    resume = Resume(user=user, file_name="resume.txt", file_type="txt", extracted_text=original_text)
    job_description = JobDescription(
        user=user,
        title="Data Analyst",
        description="Analyze business data using Python and SQL.",
    )
    analysis = Analysis(
        user=user,
        resume=resume,
        job_description=job_description,
        ats_score=70,
        job_match_score=65,
        skill_score=70,
        keyword_score=60,
        experience_score=65,
        education_score=80,
        resume_quality_score=75,
        overall_score=70,
    )
    db_session.add(analysis)
    db_session.commit()

    monkeypatch.setattr(generated_resumes, "_storage_root", lambda: tmp_path)
    client.app.dependency_overrides[get_current_user] = lambda: user
    try:
        first = client.post(f"/api/analyses/{analysis.id}/generate-resume")
        second = client.post(f"/api/analyses/{analysis.id}/generate-resume")

        assert first.status_code == 200, first.text
        assert second.status_code == 200, second.text
        first_id = first.json()["generated_resume_id"]
        second_id = second.json()["generated_resume_id"]

        details = client.get(f"/api/generated-resumes/{first_id}")
        assert details.status_code == 200
        assert details.json()["analysis_id"] == analysis.id
        assert details.json()["optimized_text"]

        first_record = db_session.get(generated_resumes.GeneratedResume, first_id)
        initial_pdf_path = first_record.pdf_file_path
        template = client.put(
            f"/api/generated-resumes/{first_id}/template",
            json={"template_name": "Minimal"},
        )
        assert template.status_code == 200
        assert template.json()["template_name"] == "Minimal"

        pdf = client.get(f"/api/generated-resumes/{first_id}/download/pdf")
        docx = client.get(f"/api/generated-resumes/{first_id}/download/docx")
        assert pdf.status_code == 200
        assert pdf.content.startswith(b"%PDF")
        assert docx.status_code == 200
        assert docx.content.startswith(b"PK")

        second_record = db_session.get(generated_resumes.GeneratedResume, second_id)
        assert first_record.template_name == "Minimal"
        assert first_record.pdf_file_path != initial_pdf_path
        assert first_record.pdf_file_path != second_record.pdf_file_path
        assert first_record.docx_file_path != second_record.docx_file_path
        assert resume.extracted_text == original_text
    finally:
        client.app.dependency_overrides.pop(get_current_user, None)