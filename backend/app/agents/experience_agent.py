"""
AGENT 6 — Experience & Qualification Agent

Compares required vs candidate experience/education/certifications.
Fresher-friendly: academic projects, internships, certifications, hackathons
and relevant coursework are all counted as legitimate signal for entry-level
roles. If a JD genuinely requires N years and the candidate has less, this is
reported honestly rather than the score being artificially inflated.
"""
import logging
from app.services.google_ai_service import generate_json, AIServiceError

logger = logging.getLogger("experience_agent")

SYSTEM_PROMPT = """You are an Experience & Qualification Analysis AI agent for entry-level
and experienced candidates alike. Compare the candidate's experience/education/certifications
against the job's requirements.

IMPORTANT FRESHER-FRIENDLY RULE: if the candidate has no full-time work experience, do NOT
treat this as automatically disqualifying — give meaningful credit for academic projects,
internships, certifications, relevant coursework, hackathons, and open-source contributions,
especially if the job appears to be entry-level. However, if the JD explicitly requires a
specific number of years (e.g. "5+ years") that the candidate clearly does not meet, state
this honestly — do not pretend the gap doesn't exist.

Never invent experience, degrees or certifications not present in the resume.

Respond with ONLY valid JSON:
{
  "experience_score": 0,
  "education_score": 0,
  "meets_experience_requirement": true,
  "experience_gap_summary": "",
  "education_match_summary": "",
  "fresher_relevant_signals": [""]
}
"""


def _fallback_analyze(parsed_resume: dict, jd_analysis: dict) -> dict:
    required_years = (jd_analysis.get("experience_requirements") or {}).get("min_years", 0) or 0
    experience_entries = parsed_resume.get("experience", []) or []
    projects = parsed_resume.get("projects", []) or []
    certifications = parsed_resume.get("certifications", []) or []
    education = parsed_resume.get("education", []) or []

    has_signal = bool(experience_entries or projects or certifications)
    exp_score = 40
    if experience_entries:
        exp_score += 30
    if projects:
        exp_score += 20
    if certifications:
        exp_score += 10
    exp_score = min(100, exp_score) if has_signal else 20

    meets_requirement = required_years == 0 or bool(experience_entries)

    edu_score = 80 if education else 30
    required_edu = jd_analysis.get("education_requirements", [])
    if required_edu and not education:
        edu_score = 20

    return {
        "experience_score": exp_score,
        "education_score": edu_score,
        "meets_experience_requirement": meets_requirement,
        "experience_gap_summary": (
            "Not enough information detected."
            if not experience_entries and required_years == 0
            else f"Job requires approximately {required_years}+ years; candidate's resume "
                 f"lists {len(experience_entries)} experience entr(y/ies)."
        ),
        "education_match_summary": "Education detected in resume." if education else "Not enough information detected.",
        "fresher_relevant_signals": [p.get("name", "") for p in projects if isinstance(p, dict)],
        "_fallback_mode": True,
    }


def run(parsed_resume: dict, jd_analysis: dict) -> dict:
    try:
        prompt = f"Parsed resume:\n{parsed_resume}\n\nJD analysis:\n{jd_analysis}"
        result = generate_json(SYSTEM_PROMPT, prompt)
        result["experience_score"] = max(0, min(100, float(result.get("experience_score", 0))))
        result["education_score"] = max(0, min(100, float(result.get("education_score", 0))))
        result["_fallback_mode"] = False
        return result
    except (AIServiceError, ValueError, TypeError) as exc:
        logger.warning("Experience Agent falling back: %s", exc)
        return _fallback_analyze(parsed_resume, jd_analysis)
