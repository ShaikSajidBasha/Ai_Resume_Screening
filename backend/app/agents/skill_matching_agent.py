"""
AGENT 4 — Skill Matching Agent

Compares resume skills (from Agent 1) against JD required/preferred skills
(from Agent 2) using semantic matching (an "AWS" on resume should match
"Amazon Web Services" in JD, etc). The LLM proposes the semantic match; the
skill-match PERCENTAGE itself is always computed deterministically in Python
from the classified lists, never invented by the AI.
"""
import logging
from app.services.google_ai_service import generate_json, AIServiceError

logger = logging.getLogger("skill_matching_agent")

SYSTEM_PROMPT = """You are a Skill Matching AI agent. You are given a candidate's resume
skills and a job's required + preferred skills. Perform SEMANTIC matching (recognize
synonyms/abbreviations, e.g. "ML" == "Machine Learning", "AWS" == "Amazon Web Services").
Do not invent skills that are not in either list. Respond with ONLY valid JSON:
{
  "exact_matches": [""],
  "related_matches": [{"resume_skill": "", "matches_jd_skill": ""}],
  "missing_required_skills": [""],
  "missing_preferred_skills": [""],
  "additional_resume_skills": [""]
}
"""


def _fallback_match(resume_skills: list, required_skills: list, preferred_skills: list) -> dict:
    resume_lower = {s.lower().strip() for s in resume_skills if s}
    required_names = [s.get("name", s) if isinstance(s, dict) else s for s in required_skills]
    preferred_names = [s.get("name", s) if isinstance(s, dict) else s for s in preferred_skills]

    exact_matches = [r for r in required_names if r.lower().strip() in resume_lower]
    missing_required = [r for r in required_names if r.lower().strip() not in resume_lower]
    missing_preferred = [p for p in preferred_names if p.lower().strip() not in resume_lower]
    all_jd_lower = {r.lower().strip() for r in required_names + preferred_names}
    additional = [s for s in resume_skills if s and s.lower().strip() not in all_jd_lower]

    return {
        "exact_matches": exact_matches,
        "related_matches": [],
        "missing_required_skills": missing_required,
        "missing_preferred_skills": missing_preferred,
        "additional_resume_skills": additional,
        "_fallback_mode": True,
    }


def run(resume_skills: list, required_skills: list, preferred_skills: list) -> dict:
    try:
        prompt = (
            f"Resume skills: {resume_skills}\n"
            f"JD required skills: {required_skills}\n"
            f"JD preferred skills: {preferred_skills}"
        )
        result = generate_json(SYSTEM_PROMPT, prompt)
        result["_fallback_mode"] = False
        return result
    except AIServiceError as exc:
        logger.warning("Skill Matching Agent falling back: %s", exc)
        return _fallback_match(resume_skills, required_skills, preferred_skills)


def compute_skill_score(match_result: dict, required_skills: list, preferred_skills: list) -> float:
    """Deterministic percentage — never left to the LLM."""
    required_names = [s.get("name", s) if isinstance(s, dict) else s for s in required_skills]
    preferred_names = [s.get("name", s) if isinstance(s, dict) else s for s in preferred_skills]

    total_required = len(required_names)
    total_preferred = len(preferred_names)
    if total_required == 0 and total_preferred == 0:
        return 0.0

    matched_required = len(match_result.get("exact_matches", [])) + len(match_result.get("related_matches", []))
    matched_required = min(matched_required, total_required) if total_required else 0

    matched_preferred = max(0, total_preferred - len(match_result.get("missing_preferred_skills", [])))

    # Required skills weigh 80% of this sub-score, preferred skills 20%
    required_ratio = (matched_required / total_required) if total_required else 1.0
    preferred_ratio = (matched_preferred / total_preferred) if total_preferred else 1.0

    score = (required_ratio * 0.8 + preferred_ratio * 0.2) * 100
    return round(max(0.0, min(100.0, score)), 2)
