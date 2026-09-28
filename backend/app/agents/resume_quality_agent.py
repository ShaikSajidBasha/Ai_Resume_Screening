"""
AGENT 7 — Resume Quality Agent

Analyzes grammar, clarity, conciseness, professional tone, and whether
achievements are quantified. Suggests improved phrasing WITHOUT fabricating
new accomplishments — only rewording what already exists.
"""
import logging
from app.services.google_ai_service import generate_json, AIServiceError

logger = logging.getLogger("resume_quality_agent")

SYSTEM_PROMPT = """You are a Resume Writing Quality AI agent. Analyze the resume text for:
grammar issues, clarity, conciseness, professional tone, repetition, weak/vague wording,
and whether achievements include measurable/quantified outcomes. For each improvement
suggestion, you MUST base the "suggested" text only on details already present in the
"current" text — do not invent new tools, metrics, or outcomes that are not implied by
the original. Respond with ONLY valid JSON:
{
  "resume_quality_score": 0,
  "grammar_issues": [""],
  "weak_phrases": [{"current": "", "suggested": ""}],
  "quantification_gaps": [""]
}
"""


def _fallback_analyze(resume_text: str) -> dict:
    weak_markers = ["worked on", "responsible for", "helped with", "involved in"]
    weak_found = [m for m in weak_markers if m in resume_text.lower()]
    has_numbers = any(ch.isdigit() for ch in resume_text)

    score = 60
    if weak_found:
        score -= 10 * len(weak_found)
    if has_numbers:
        score += 15
    score = max(0, min(100, score))

    return {
        "resume_quality_score": score,
        "grammar_issues": [],
        "weak_phrases": [
            {"current": phrase, "suggested": "Use a stronger action verb and, where true, add a measurable outcome."}
            for phrase in weak_found
        ],
        "quantification_gaps": [] if has_numbers else ["Consider adding measurable results (%, counts, time saved) where genuinely applicable."],
        "_fallback_mode": True,
    }


def run(resume_text: str) -> dict:
    try:
        result = generate_json(SYSTEM_PROMPT, f"Resume text:\n\n{resume_text[:12000]}")
        result["resume_quality_score"] = max(0, min(100, float(result.get("resume_quality_score", 0))))
        result["_fallback_mode"] = False
        return result
    except (AIServiceError, ValueError, TypeError) as exc:
        logger.warning("Resume Quality Agent falling back: %s", exc)
        return _fallback_analyze(resume_text)
