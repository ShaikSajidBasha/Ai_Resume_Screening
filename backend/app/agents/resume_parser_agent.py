"""
AGENT 1 — Resume Parser Agent

Extracts structured information from raw resume text using the LLM for
semantic understanding, with a regex-based deterministic fallback so the
pipeline still works if the AI call fails.
"""
import re
import logging
from app.services.google_ai_service import generate_json, AIServiceError
from app.utils.text_extraction_helpers import extract_known_skills, extract_section_lines

logger = logging.getLogger("resume_parser_agent")

SYSTEM_PROMPT = """You are a Resume Parsing AI agent inside an ATS analysis system.
Extract ONLY information that is explicitly present in the resume text. Never invent
skills, experience, education, or certifications that are not stated. If a field is not
present, return an empty string, empty list, or "Not enough information detected." as
appropriate. Respond with ONLY valid JSON matching this schema:
{
  "personal_info": {"name": "", "email": "", "phone": "", "links": []},
  "summary": "",
  "education": [{"degree": "", "institution": "", "year": ""}],
  "skills": [""],
  "experience": [{"title": "", "company": "", "duration": "", "description": ""}],
  "projects": [{"name": "", "description": "", "technologies": [""]}],
  "certifications": [""],
  "achievements": [""]
}
"""

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"(\+?\d[\d\-\s]{8,14}\d)")


def _fallback_parse(resume_text: str) -> dict:
    """Very simple deterministic fallback so the app degrades gracefully without an API key."""
    email_match = EMAIL_RE.search(resume_text)
    phone_match = PHONE_RE.search(resume_text)
    lines = [l.strip() for l in resume_text.splitlines() if l.strip()]
    name_guess = lines[0][:80] if lines else ""

    skills_section = extract_section_lines(resume_text, "skills")
    skills = []
    if skills_section:
        for line in skills_section:
            skills.extend([s.strip() for s in re.split(r",|\u2022|\|", line) if s.strip()])
    if not skills:
        skills = extract_known_skills(resume_text)

    education_lines = extract_section_lines(resume_text, "education")
    education = [{"degree": e, "institution": "", "year": ""} for e in education_lines]

    certification_lines = extract_section_lines(resume_text, "certifications")

    experience_lines = extract_section_lines(resume_text, "experience")
    experience = [{"title": e, "company": "", "duration": "", "description": e} for e in experience_lines[:5]]

    project_header_re = re.compile(r"(?im)^\s*(academic\s+)?projects?\s*:?\s*$")
    projects = []
    lines_all = resume_text.splitlines()
    for i, line in enumerate(lines_all):
        if project_header_re.match(line.strip()):
            for candidate in lines_all[i + 1:i + 10]:
                stripped = candidate.strip(" \t-•*")
                if not stripped:
                    if projects:
                        break
                    continue
                projects.append({"name": stripped[:100], "description": stripped, "technologies": []})
            break

    return {
        "personal_info": {
            "name": name_guess,
            "email": email_match.group(0) if email_match else "",
            "phone": phone_match.group(0) if phone_match else "",
            "links": re.findall(r"https?://\S+", resume_text),
        },
        "summary": "Not enough information detected.",
        "education": education,
        "skills": skills,
        "experience": experience,
        "projects": projects,
        "certifications": certification_lines,
        "achievements": [],
        "_fallback_mode": True,
    }


def run(resume_text: str) -> dict:
    try:
        result = generate_json(SYSTEM_PROMPT, f"Resume text:\n\n{resume_text[:12000]}")
        result["_fallback_mode"] = False
        return result
    except AIServiceError as exc:
        logger.warning("Resume Parser Agent falling back to deterministic parsing: %s", exc)
        return _fallback_parse(resume_text)
