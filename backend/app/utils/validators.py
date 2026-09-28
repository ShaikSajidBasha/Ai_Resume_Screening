"""
File validation helpers: extension, size, basic content sanity checks.
"""
from fastapi import UploadFile
from app.core.config import settings


class FileValidationError(Exception):
    pass


def validate_resume_file(file: UploadFile, file_bytes: bytes) -> str:
    """Returns the normalized extension (e.g. '.pdf') or raises FileValidationError."""
    filename = (file.filename or "").lower()
    ext = None
    for allowed in settings.ALLOWED_RESUME_EXTENSIONS:
        if filename.endswith(allowed):
            ext = allowed
            break

    if ext is None:
        raise FileValidationError("Unsupported file type. Please upload PDF or DOCX.")

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise FileValidationError(
            f"File too large. Maximum allowed size is {settings.MAX_UPLOAD_SIZE_MB}MB."
        )

    if len(file_bytes) == 0:
        raise FileValidationError("Uploaded file is empty.")

    return ext


def validate_job_description(text: str) -> None:
    if not text or len(text.strip()) < 20:
        raise FileValidationError("Please provide a Job Description.")
