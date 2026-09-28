import io
import pytest
from fastapi import UploadFile
from app.utils.validators import validate_resume_file, FileValidationError


def _make_upload(filename: str) -> UploadFile:
    return UploadFile(filename=filename, file=io.BytesIO(b"dummy"))


def test_rejects_unsupported_extension():
    upload = _make_upload("resume.exe")
    with pytest.raises(FileValidationError):
        validate_resume_file(upload, b"dummy")


def test_accepts_pdf_extension():
    upload = _make_upload("resume.pdf")
    ext = validate_resume_file(upload, b"dummy-bytes")
    assert ext == ".pdf"
