"""
AGENT 3 — ATS Analysis Agent

Assesses ATS *formatting and content* compatibility of the resume text.
Note: the numerical ats_score returned here is an AI *estimate signal* that
feeds into the deterministic Scoring Agent — it is not the final displayed
score by itself. This is clearly an AI-based estimate, not a real ATS engine.
"""
import logging
from app.services.google_ai_service import generate_json, AIServiceError

logger = logging.getLogger("ats_agent")

SYSTEM_PROMPT = """You are an ATS (Applicant Tracking System) Compatibility Analysis AI agent.
Evaluate the resume text for ATS-friendliness: section clarity, standard headings,
absence of complex tables/columns/graphics artifacts in the raw text, presence of a
skills section, presence of contact info, presence of an experience/education section,
use of standard date formats, and measurable achievements. Give an ats_score from 0-100
representing your estimate of ATS parseability and completeness ONLY — do not factor in
job-fit. Respond with ONLY valid JSON:
{
  "ats_score": 0,
  "issues": [""],
  "strengths": [""],
  "recommendations": [""]
}
"""


def _fallback_analyze(resume_text: str) -> dict:
    issues = []
    strengths = []
    lower = resume_text.lower()

    has_email = "@" in resume_text
    has_skills_section = "skill" in lower
    has_education_section = "education" in lower
    has_experience_section = any(k in lower for k in ["experience", "internship", "work history"])

    score = 40
    if has_email:
        strengths.append("Contact details detected.")
        score += 10
    else:
        issues.append("No email address detected — ATS systems rely on this for contact parsing.")

    if has_skills_section:
        strengths.append("Skills section detected.")
        score += 15
    else:
        issues.append("No clearly labeled Skills section detected.")

    if has_education_section:
        strengths.append("Education section detected.")
        score += 10
    else:
        issues.append("No clearly labeled Education section detected.")

    if has_experience_section:
        strengths.append("Experience/Projects/Internship section detected.")
        score += 15
    else:
        issues.append("No Experience, Internship, or Projects section detected.")

    if len(resume_text) < 800:
        issues.append("Resume content appears short; ensure all relevant sections are included.")
    else:
        score += 10

    score = max(0, min(100, score))

    return {
        "ats_score": score,
        "issues": issues,
        "strengths": strengths,
        "recommendations": [
            "Use standard section headings such as Skills, Experience, Education, Projects.",
            "Avoid embedding text inside images or complex multi-column layouts.",
            "Use consistent, unambiguous date formats (e.g., Jan 2024 – Present).",
        ],
        "_fallback_mode": True,
    }


def run(resume_text: str) -> dict:
    try:
        result = generate_json(SYSTEM_PROMPT, f"Resume text:\n\n{resume_text[:12000]}")
        result["ats_score"] = max(0, min(100, float(result.get("ats_score", 0))))
        result["_fallback_mode"] = False
        return result
    except (AIServiceError, ValueError, TypeError) as exc:
        logger.warning("ATS Agent falling back: %s", exc)
        return _fallback_analyze(resume_text)
