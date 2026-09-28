"""
AGENT 8 — Scoring Agent

Purely deterministic. Takes the sub-scores produced by upstream agents and
combines them using configurable weights from app.core.config. The LLM never
determines the final numerical score — this function is the single source
of truth for the math, which keeps the system auditable and reproducible.
"""
from app.core.config import settings


def compute_overall_score(sub_scores: dict) -> float:
    """
    sub_scores keys expected: ats_score, skill_score, keyword_score,
    experience_score, education_score, resume_quality_score
    """
    weights = settings.SCORE_WEIGHTS
    total = 0.0
    weight_sum = 0.0
    for key, weight in weights.items():
        value = sub_scores.get(key)
        if value is None:
            continue
        total += float(value) * weight
        weight_sum += weight

    if weight_sum == 0:
        return 0.0

    # Renormalize in case a sub-score was unavailable, so partial data doesn't unfairly tank the score
    overall = total / weight_sum
    return round(max(0.0, min(100.0, overall)), 2)


def compute_job_match_score(skill_score: float, keyword_score: float, experience_score: float) -> float:
    """
    A secondary, JD-fit-focused score shown alongside ATS score, distinct from
    the overall weighted score. Simple average of the three JD-relevance signals.
    """
    values = [v for v in [skill_score, keyword_score, experience_score] if v is not None]
    if not values:
        return 0.0
    return round(sum(values) / len(values), 2)


def resolve_status_label(overall_score: float) -> str:
    for threshold, label in settings.STATUS_THRESHOLDS:
        if overall_score >= threshold:
            return label
    return settings.STATUS_THRESHOLDS[-1][1]
