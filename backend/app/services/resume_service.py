"""
Handles resume file ingestion: validation + text extraction, independent of
the AI pipeline (so upload can succeed even if AI analysis happens later).
"""
from fastapi import UploadFile

from app.utils.validators import validate_resume_file, FileValidationError
from app.utils.pdf_parser import extract_text_from_pdf, PDFExtractionError
from app.utils.docx_parser import extract_text_from_docx, DOCXExtractionError


class ResumeProcessingError(Exception):
    pass


def extract_resume_text(file: UploadFile, file_bytes: bytes) -> tuple:
    """Returns (extracted_text, extension)."""
    try:
        ext = validate_resume_file(file, file_bytes)
    except FileValidationError as exc:
        raise ResumeProcessingError(str(exc)) from exc

    try:
        if ext == ".pdf":
            text = extract_text_from_pdf(file_bytes)
        elif ext == ".docx":
            text = extract_text_from_docx(file_bytes)
        else:  # .txt
            text = file_bytes.decode("utf-8", errors="ignore").strip()
            if not text or len(text) < 30:
                raise ResumeProcessingError("Unable to detect meaningful resume content.")
    except (PDFExtractionError, DOCXExtractionError) as exc:
        raise ResumeProcessingError(str(exc)) from exc

    return text, ext
