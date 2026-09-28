"""
AGENT 2 — Job Description Analyzer Agent

Extracts required/preferred skills (categorized), experience & education
requirements, responsibilities, and important keywords from a Job Description.
"""
import logging
from app.services.google_ai_service import generate_json, AIServiceError
from app.utils.text_extraction_helpers import (
    extract_known_skills, extract_section_lines, extract_required_years,
)

logger = logging.getLogger("jd_analyzer_agent")

SYSTEM_PROMPT = """You are a Job Description Analysis AI agent inside an ATS system.
Extract ONLY what is explicitly stated or clearly implied in the job description.
Categorize skills into: Programming, Frameworks, Databases, Cloud, AI/ML, Tools,
Soft Skills, Domain Skills. Respond with ONLY valid JSON matching this schema:
{
  "job_title": "",
  "required_skills": [{"name": "", "category": ""}],
  "preferred_skills": [{"name": "", "category": ""}],
  "education_requirements": [""],
  "experience_requirements": {"min_years": 0, "level": "entry|mid|senior|not_specified"},
  "certifications": [""],
  "responsibilities": [""],
  "keywords": [{"keyword": "", "importance": "High|Medium|Low"}]
}
"""


def _fallback_parse(jd_text: str) -> dict:
    required_lines = extract_section_lines(jd_text, "required_skills")
    preferred_lines = extract_section_lines(jd_text, "preferred_skills")

    def _split_skills(lines):
        out = []
        for line in lines:
            out.extend([s.strip() for s in line.split(",") if s.strip()])
        return out

    required_skills = _split_skills(required_lines) or extract_known_skills(jd_text)
    preferred_skills = _split_skills(preferred_lines)
    # avoid double-counting a skill as both required and preferred
    preferred_skills = [s for s in preferred_skills if s not in required_skills]

    education_lines = extract_section_lines(jd_text, "education")
    required_years = extract_required_years(jd_text)
    level = "entry" if required_years <= 1 else ("senior" if required_years >= 5 else "mid")

    keywords = (
        [{"keyword": s, "importance": "High"} for s in required_skills]
        + [{"keyword": s, "importance": "Medium"} for s in preferred_skills]
    )

    return {
        "job_title": "Not enough information detected.",
        "required_skills": [{"name": s, "category": ""} for s in required_skills],
        "preferred_skills": [{"name": s, "category": ""} for s in preferred_skills],
        "education_requirements": education_lines,
        "experience_requirements": {"min_years": required_years, "level": level},
        "certifications": [],
        "responsibilities": [],
        "keywords": keywords,
        "_fallback_mode": True,
    }


def run(jd_text: str, job_title_hint: str = "") -> dict:
    try:
        prompt = f"Job Title (from form): {job_title_hint}\n\nJob Description:\n\n{jd_text[:12000]}"
        result = generate_json(SYSTEM_PROMPT, prompt)
        result["_fallback_mode"] = False
        return result
    except AIServiceError as exc:
        logger.warning("JD Analyzer Agent falling back: %s", exc)
        fb = _fallback_parse(jd_text)
        fb["job_title"] = job_title_hint or fb["job_title"]
        return fb
