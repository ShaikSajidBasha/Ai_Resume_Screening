"""
PDF text extraction using PyMuPDF (fitz).
"""
import fitz  # PyMuPDF


class PDFExtractionError(Exception):
    pass


def extract_text_from_pdf(file_bytes: bytes) -> str:
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as exc:
        raise PDFExtractionError("Unable to open PDF file.") from exc

    text_parts = []
    for page in doc:
        text_parts.append(page.get_text())
    doc.close()

    text = "\n".join(text_parts).strip()
    if not text or len(text) < 30:
        raise PDFExtractionError(
            "Unable to extract text from this PDF. Please upload a text-based PDF."
        )
    return text
