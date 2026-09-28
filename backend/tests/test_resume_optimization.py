import os

import pymupdf
from docx import Document

from app.agents.resume_optimization_agent import run as optimize_resume
from app.agents.resume_validation_agent import run as validate_resume
from app.agents.resume_formatting_agent import run as format_resume
from app.services.resume_document_service import generate_resume_documents


ORIGINAL_RESUME = """
Aarav Sharma
Email: aarav.sharma@gmail.com | Phone: +91 9876543210

Professional Summary
Computer Science graduate with experience in Python, SQL, and machine learning projects. Interested in software development and data-driven problem solving.

Skills
Python, SQL, Java, C++, Machine Learning, Tableau

Projects
Student Performance Prediction System | Python, scikit-learn, SQL
Built a machine learning model to predict student performance using academic features.

Education
B.Tech in Computer Science, XYZ University, 2024
CGPA: 8.7

Certifications
Google Data Analytics Certificate
"""

JOB_DESCRIPTION = """
Python Developer
Need Python, SQL, machine learning, software engineering, backend development
"""

ANALYSIS_RESULT = {
    "missing_skills": ["FastAPI"],
    "missing_keywords": [{"keyword": "FastAPI", "status": "Missing"}],
    "recommendations": [{"category": "Skill gap", "recommendation": "Add FastAPI experience if available."}],
    "matching_skills": ["Python", "SQL", "Machine Learning"],
    "ats_issues": ["Add stronger project impact statements"],
}


def test_resume_optimization_agent_preserves_factual_information():
    result = optimize_resume(ORIGINAL_RESUME, JOB_DESCRIPTION, ANALYSIS_RESULT, [])

    assert result["professional_summary"]
    assert "Python" in result["skills"]["Programming Languages"] or "Python" in result["skills"]["Other Technical Skills"]
    assert "Google Data Analytics Certificate" in result["certifications"] or "Google Data Analytics Certificate" in result["education"]
    assert "FastAPI" not in result["skills"]["Programming Languages"]


def test_resume_optimization_does_not_repeat_projects_or_sections():
    original = """Alex Smith
alex.smith@example.com

Technical Skills
Programming Languages: Python, SQL

Projects
Mini AI Chatbot
Built a web-based AI chatbot.

Projects
Mini AI Chatbot
Built a web-based AI chatbot.
"""

    result = optimize_resume(original, JOB_DESCRIPTION, ANALYSIS_RESULT, [])

    assert result["experience"] == ""
    assert result["optimized_text"].count("Projects") == 1
    assert result["optimized_text"].count("Built a web-based AI chatbot.") == 1
    assert "Original education details preserved." not in result["optimized_text"]


def test_resume_validation_agent_detects_unsupported_information():
    original = ORIGINAL_RESUME
    modified = ORIGINAL_RESUME + "\n\nExperience\nSenior Software Engineer at Google\n"
    result = validate_resume(original, {"professional_summary": modified})

    assert result["is_valid"] is False
    assert result["fabricated_content"]


def test_resume_formatting_agent_returns_aligned_sections():
    optimized = optimize_resume(ORIGINAL_RESUME, JOB_DESCRIPTION, ANALYSIS_RESULT, [])
    formatted = format_resume(optimized)

    assert formatted["recommended_sections"]
    assert "Professional Summary" in formatted["recommended_sections"]
    assert formatted["formatting"]["layout"] == "single-column"


def test_document_generation_creates_pdf_and_docx(tmp_path):
    output_dir = tmp_path / "generated_resume"
    output_dir.mkdir()
    long_resume = "\n".join(
        ["Alex Smith", "Professional Summary", "Python developer with project experience.", "Python Developer"]
        + [f"Project detail {index}: delivered measurable improvements using Python and SQL." for index in range(80)]
    )

    pdf_path, docx_path = generate_resume_documents(
        optimized_text=long_resume,
        output_dir=str(output_dir),
        filename_prefix="resume_v1",
    )

    assert os.path.exists(pdf_path)
    assert os.path.exists(docx_path)
    assert pdf_path.endswith(".pdf")
    assert docx_path.endswith(".docx")
    with pymupdf.open(pdf_path) as pdf:
        assert len(pdf) == 1
    docx_paragraphs = [paragraph.text for paragraph in Document(docx_path).paragraphs if paragraph.text]
    assert docx_paragraphs.count("Python Developer") == 1
