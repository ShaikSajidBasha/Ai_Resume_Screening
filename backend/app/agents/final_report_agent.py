"""
AGENT 10 — Final Report Agent

Combines the outputs of every upstream agent plus the deterministic scores
into one structured, human-readable screening report. The narrative summary
is AI-generated for readability, but every number it references comes from
the deterministic Scoring Agent — the LLM is not allowed to alter scores here.
"""
import logging
from app.services.google_ai_service import generate_json, AIServiceError

logger = logging.getLogger("final_report_agent")

SYSTEM_PROMPT = """You are the Final Report AI agent in a resume screening pipeline.
You are given the final deterministic scores and every upstream agent's findings.
Write a concise (4-6 sentence) final_summary in a professional recruitment-analysis
tone, referencing the ALREADY-COMPUTED scores and status exactly as given (do not
recalculate or contradict them). Be honest about gaps; do not oversell weak matches.
Respond with ONLY valid JSON:
{ "final_summary": "" }
"""


def _fallback_summary(candidate_name: str, job_title: str, overall_score: float, status: str,
                       matching_skills: list, missing_skills: list) -> str:
    name_part = candidate_name or "The candidate"
    return (
        f"{name_part}'s resume was evaluated against the '{job_title}' role and received an "
        f"overall AI-estimated match score of {overall_score}/100 ({status}). "
        f"Strengths include alignment on {', '.join(matching_skills[:3]) if matching_skills else 'several core areas'}. "
        f"Key gaps to address include {', '.join(missing_skills[:3]) if missing_skills else 'a few JD-specific keywords and skills'}. "
        "This is an AI-generated estimate intended to support resume optimization, not a hiring decision."
    )


def run(report_context: dict) -> dict:
    try:
        result = generate_json(SYSTEM_PROMPT, f"Report context:\n{report_context}")
        if "final_summary" not in result or not result["final_summary"]:
            raise ValueError("empty final_summary")
        result["_fallback_mode"] = False
        return result
    except (AIServiceError, ValueError) as exc:
        logger.warning("Final Report Agent falling back: %s", exc)
        summary = _fallback_summary(
            candidate_name=report_context.get("candidate_name", ""),
            job_title=report_context.get("job_title", ""),
            overall_score=report_context.get("overall_score", 0),
            status=report_context.get("status", ""),
            matching_skills=report_context.get("matching_skills", []),
            missing_skills=report_context.get("missing_skills", []),
        )
        return {"final_summary": summary, "_fallback_mode": True}
