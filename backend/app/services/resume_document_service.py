import os
from typing import Tuple
from xml.sax.saxutils import escape

from docx import Document
from docx.shared import Mm, Pt
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import KeepInFrame, Paragraph, SimpleDocTemplate


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def generate_resume_documents(
    optimized_text: str,
    output_dir: str,
    filename_prefix: str = "resume",
    template_name: str = "ATS Professional",
) -> Tuple[str, str]:
    _ensure_dir(output_dir)

    template_styles = {
        "ATS Professional": {"font": "Arial", "font_size": 9, "margin": 12, "pdf_font": "Helvetica", "pdf_size": 9},
        "Modern Professional": {"font": "Calibri", "font_size": 9, "margin": 12, "pdf_font": "Helvetica", "pdf_size": 9},
        "Minimal": {"font": "Arial", "font_size": 8, "margin": 10, "pdf_font": "Helvetica", "pdf_size": 8},
    }
    style_options = template_styles.get(template_name, template_styles["ATS Professional"])

    pdf_path = os.path.join(output_dir, f"{filename_prefix}.pdf")
    docx_path = os.path.join(output_dir, f"{filename_prefix}.docx")

    doc = Document()
    doc.styles['Normal'].font.name = style_options["font"]
    doc.styles['Normal'].font.size = Pt(style_options["font_size"])
    doc.styles['Normal'].paragraph_format.space_after = Pt(1)
    doc.styles['Normal'].paragraph_format.line_spacing = 1
    doc.styles['Heading 2'].font.name = style_options["font"]
    doc.styles['Heading 2'].font.size = Pt(style_options["font_size"] + 1)
    doc.styles['Heading 2'].font.bold = True
    doc.styles['Heading 2'].paragraph_format.space_before = Pt(3)
    doc.styles['Heading 2'].paragraph_format.space_after = Pt(1)
    doc.styles['Heading 2'].paragraph_format.keep_with_next = True
    doc.sections[0].page_width = Mm(210)
    doc.sections[0].page_height = Mm(297)
    doc.sections[0].left_margin = Mm(style_options["margin"])
    doc.sections[0].right_margin = Mm(style_options["margin"])
    doc.sections[0].top_margin = Mm(style_options["margin"])
    doc.sections[0].bottom_margin = Mm(style_options["margin"])

    seen_lines = set()
    for line in optimized_text.splitlines():
        cleaned_line = line.strip()
        normalized_line = " ".join(cleaned_line.split()).casefold()
        if not cleaned_line or normalized_line in seen_lines:
            continue
        seen_lines.add(normalized_line)
        paragraph = doc.add_paragraph(cleaned_line)
        if cleaned_line.lower() in {
            "professional summary", "technical skills", "education", "experience",
            "projects", "certifications", "achievements", "languages",
        }:
            paragraph.style = 'Heading 2'

    doc.save(docx_path)

    styles = getSampleStyleSheet()
    story = []
    style = styles["Normal"]
    style.fontName = style_options["pdf_font"]
    style.fontSize = style_options["pdf_size"]
    style.leading = style_options["pdf_size"] * 1.15
    style.spaceAfter = 1
    style.textColor = colors.black
    heading_style = ParagraphStyle(
        "ResumeHeading",
        parent=style,
        fontName=f"{style_options['pdf_font']}-Bold",
        fontSize=style_options["pdf_size"] + 1,
        leading=(style_options["pdf_size"] + 1) * 1.15,
        spaceBefore=3,
        spaceAfter=1,
        keepWithNext=True,
    )
    name_style = ParagraphStyle(
        "ResumeName",
        parent=style,
        fontName=f"{style_options['pdf_font']}-Bold",
        fontSize=style_options["pdf_size"] + 4,
        leading=(style_options["pdf_size"] + 4) * 1.15,
        spaceAfter=2,
    )
    seen_lines = set()
    section_headings = {
        "professional summary", "technical skills", "education", "experience",
        "projects", "certifications", "achievements", "languages",
    }
    for line in optimized_text.splitlines():
        cleaned_line = line.strip()
        normalized_line = " ".join(cleaned_line.split()).casefold()
        if not cleaned_line or normalized_line in seen_lines:
            continue
        seen_lines.add(normalized_line)
        paragraph_style = name_style if not story else (
            heading_style if normalized_line in section_headings else style
        )
        story.append(Paragraph(escape(cleaned_line), paragraph_style))
    page_margin = 24
    page_content = KeepInFrame(
        A4[0] - page_margin * 2,
        A4[1] - page_margin * 2,
        story,
        mode="shrink",
    )
    SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=page_margin,
        rightMargin=page_margin,
        topMargin=page_margin,
        bottomMargin=page_margin,
    ).build([page_content])

    return pdf_path, docx_path
