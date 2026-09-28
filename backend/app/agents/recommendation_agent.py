"""
AGENT 9 — Recommendation Agent

Generates personalized, prioritized recommendations grounded strictly in the
gaps identified by upstream agents (missing skills/keywords, ATS issues,
quality issues, experience gaps). Never tells the candidate to falsely claim
a skill or fabricate experience.
"""
import logging
from app.services.google_ai_service import generate_json, AIServiceError

logger = logging.getLogger("recommendation_agent")

SYSTEM_PROMPT = """You are a Career Recommendation AI agent. Using ONLY the gaps and
issues provided (missing skills, missing keywords, ATS issues, resume quality issues,
experience gaps), produce actionable, honest recommendations. Categories to use:
Skills, Keywords, Projects, Experience, Education, Resume Formatting, Grammar,
Achievements, Professional Summary. Each recommendation must have a priority of
HIGH, MEDIUM, or LOW. NEVER advise the candidate to claim a skill or experience they
do not have — only advise them to build/practice it or highlight it IF genuinely
applicable. Respond with ONLY valid JSON:
{
  "recommendations": [{"category": "", "recommendation": "", "priority": "HIGH|MEDIUM|LOW"}]
}
"""


def _fallback_generate(context: dict) -> dict:
    recs = []
    missing_required = context.get("missing_required_skills", [])
    if missing_required:
        recs.append({
            "category": "Skills",
            "recommendation": (
                f"Consider building genuine experience with: {', '.join(missing_required[:5])}. "
                "Only list these once you have real, demonstrable exposure to them."
            ),
            "priority": "HIGH",
        })

    missing_keywords = [k["keyword"] for k in context.get("keyword_status", []) if k.get("status") == "Missing"]
    if missing_keywords:
        recs.append({
            "category": "Keywords",
            "recommendation": (
                f"Naturally incorporate relevant terms if applicable: {', '.join(missing_keywords[:5])}. "
                "Do not stuff keywords that don't reflect real experience."
            ),
            "priority": "MEDIUM",
        })

    for issue in context.get("ats_issues", [])[:3]:
        recs.append({"category": "Resume Formatting", "recommendation": issue, "priority": "MEDIUM"})

    for gap in context.get("quantification_gaps", []):
        recs.append({"category": "Achievements", "recommendation": gap, "priority": "LOW"})

    if not context.get("meets_experience_requirement", True):
        recs.append({
            "category": "Experience",
            "recommendation": context.get("experience_gap_summary", "Experience gap identified relative to the JD."),
            "priority": "HIGH",
        })

    if not recs:
        recs.append({
            "category": "Professional Summary",
            "recommendation": "Resume appears well aligned with the job description overall.",
            "priority": "LOW",
        })

    return {"recommendations": recs, "_fallback_mode": True}


def run(context: dict) -> dict:
    try:
        result = generate_json(SYSTEM_PROMPT, f"Context:\n{context}")
        result["_fallback_mode"] = False
        return result
    except AIServiceError as exc:
        logger.warning("Recommendation Agent falling back: %s", exc)
        return _fallback_generate(context)
