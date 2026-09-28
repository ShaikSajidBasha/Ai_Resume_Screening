"""
Thin wrapper around the deterministic Scoring Agent, exposed as a service so
API routers and the analysis orchestrator don't reach into agents directly
for pure-math operations.
"""
from app.agents import scoring_agent
from app.core.config import settings


def score_analysis(sub_scores: dict) -> dict:
    overall = scoring_agent.compute_overall_score(sub_scores)
    job_match = scoring_agent.compute_job_match_score(
        sub_scores.get("skill_score", 0),
        sub_scores.get("keyword_score", 0),
        sub_scores.get("experience_score", 0),
    )
    status = scoring_agent.resolve_status_label(overall)
    return {
        "overall_score": overall,
        "job_match_score": job_match,
        "status": status,
        "weights": settings.SCORE_WEIGHTS,
    }
