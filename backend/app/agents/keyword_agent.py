"""
AGENT 5 — Keyword Matching Agent

Compares JD keywords against the full resume text (skills, experience,
projects, summary combined). Classifies as Found / Partially Found / Missing.
Never recommends keyword stuffing.
"""
import logging
from app.services.google_ai_service import generate_json, AIServiceError

logger = logging.getLogger("keyword_agent")

SYSTEM_PROMPT = """You are a Keyword Matching AI agent for ATS analysis. Given important
JD keywords and the resume's full text, classify each keyword as "Found", "Partially Found"
(a close synonym/related term appears), or "Missing". NEVER suggest keyword stuffing —
only suggest naturally incorporating a keyword if the underlying skill/experience genuinely
applies. Respond with ONLY valid JSON:
{
  "keyword_status": [{"keyword": "", "status": "Found|Partially Found|Missing", "importance": "High|Medium|Low"}]
}
"""


def _fallback_match(keywords: list, resume_text: str) -> dict:
    lower_text = resume_text.lower()
    statuses = []
    for kw in keywords:
        name = kw.get("keyword", kw) if isinstance(kw, dict) else kw
        importance = kw.get("importance", "Medium") if isinstance(kw, dict) else "Medium"
        status = "Found" if name and name.lower().strip() in lower_text else "Missing"
        statuses.append({"keyword": name, "status": status, "importance": importance})
    return {"keyword_status": statuses, "_fallback_mode": True}


def run(keywords: list, resume_text: str) -> dict:
    try:
        prompt = f"JD keywords: {keywords}\n\nResume text:\n\n{resume_text[:10000]}"
        result = generate_json(SYSTEM_PROMPT, prompt)
        result["_fallback_mode"] = False
        return result
    except AIServiceError as exc:
        logger.warning("Keyword Agent falling back: %s", exc)
        return _fallback_match(keywords, resume_text)


def compute_keyword_score(keyword_status: list) -> float:
    """Deterministic: Found=1.0, Partially Found=0.5, Missing=0, weighted by importance."""
    if not keyword_status:
        return 0.0

    weight_map = {"High": 3, "Medium": 2, "Low": 1}
    status_value = {"Found": 1.0, "Partially Found": 0.5, "Missing": 0.0}

    total_weight = 0.0
    achieved_weight = 0.0
    for item in keyword_status:
        w = weight_map.get(item.get("importance", "Medium"), 2)
        v = status_value.get(item.get("status", "Missing"), 0.0)
        total_weight += w
        achieved_weight += w * v

    if total_weight == 0:
        return 0.0
    return round((achieved_weight / total_weight) * 100, 2)
