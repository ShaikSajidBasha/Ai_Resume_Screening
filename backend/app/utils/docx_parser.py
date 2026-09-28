"""
DOCX text extraction using python-docx.
"""
import io
import docx


class DOCXExtractionError(Exception):
    pass


def extract_text_from_docx(file_bytes: bytes) -> str:
    try:
        document = docx.Document(io.BytesIO(file_bytes))
    except Exception as exc:
        raise DOCXExtractionError("Unable to open DOCX file.") from exc

    parts = [p.text for p in document.paragraphs if p.text.strip()]
    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text.strip():
                    parts.append(cell.text)

    text = "\n".join(parts).strip()
    if not text or len(text) < 30:
        raise DOCXExtractionError("Unable to detect meaningful resume content.")
    return text
