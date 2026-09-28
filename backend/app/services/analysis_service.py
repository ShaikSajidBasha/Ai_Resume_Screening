"""
The Multi-Agent Orchestrator.

Runs every agent in sequence (Resume Parser -> JD Analyzer -> ATS -> Skill
Matching -> Keyword Matching -> Experience/Qualification -> Resume Quality ->
Scoring -> Recommendation -> Final Report), persists every agent's raw output
to `agent_results` for auditability, and writes the final analysis + related
rows to the database.
"""
import json
import logging

from sqlalchemy.orm import Session

from app.agents import (
    resume_parser_agent,
    jd_analyzer_agent,
    ats_agent,
    skill_matching_agent,
    keyword_agent,
    experience_agent,
    resume_quality_agent,
    recommendation_agent,
    final_report_agent,
)
from app.services.scoring_service import score_analysis
from app.models.analysis import Analysis, ExtractedSkill, MissingKeyword, Recommendation
from app.models.agent_result import AgentResult
from app.models.resume import Resume
from app.models.job_description import JobDescription

logger = logging.getLogger("analysis_service")


def _persist_agent_result(db: Session, analysis_id: int, agent_name: str, result: dict):
    db.add(AgentResult(analysis_id=analysis_id, agent_name=agent_name, result_json=json.dumps(result)[:60000]))


def run_full_analysis(db: Session, user_id: int, resume: Resume, job_description: JobDescription) -> Analysis:
    resume_text = resume.extracted_text
    jd_text = job_description.description

    # --- Stage 1: Resume Parser Agent ---
    parsed_resume = resume_parser_agent.run(resume_text)

    # --- Stage 2: JD Analyzer Agent ---
    jd_analysis = jd_analyzer_agent.run(jd_text, job_title_hint=job_description.title)

    # --- Stage 3: ATS Agent ---
    ats_result = ats_agent.run(resume_text)

    # --- Stage 4: Skill Matching Agent ---
    resume_skills = parsed_resume.get("skills", []) or []
    required_skills = jd_analysis.get("required_skills", []) or []
    preferred_skills = jd_analysis.get("preferred_skills", []) or []
    skill_match = skill_matching_agent.run(resume_skills, required_skills, preferred_skills)
    skill_score = skill_matching_agent.compute_skill_score(skill_match, required_skills, preferred_skills)

    # --- Stage 5: Keyword Matching Agent ---
    keywords = jd_analysis.get("keywords", []) or []
    keyword_match = keyword_agent.run(keywords, resume_text)
    keyword_score = keyword_agent.compute_keyword_score(keyword_match.get("keyword_status", []))

    # --- Stage 6: Experience & Qualification Agent ---
    experience_result = experience_agent.run(parsed_resume, jd_analysis)

    # --- Stage 7: Resume Quality Agent ---
    quality_result = resume_quality_agent.run(resume_text)

    # --- Stage 8: Scoring Agent (deterministic) ---
    sub_scores = {
        "ats_score": ats_result.get("ats_score", 0),
        "skill_score": skill_score,
        "keyword_score": keyword_score,
        "experience_score": experience_result.get("experience_score", 0),
        "education_score": experience_result.get("education_score", 0),
        "resume_quality_score": quality_result.get("resume_quality_score", 0),
    }
    scores = score_analysis(sub_scores)

    # --- Stage 9: Recommendation Agent ---
    rec_context = {
        "missing_required_skills": skill_match.get("missing_required_skills", []),
        "missing_preferred_skills": skill_match.get("missing_preferred_skills", []),
        "keyword_status": keyword_match.get("keyword_status", []),
        "ats_issues": ats_result.get("issues", []),
        "quantification_gaps": quality_result.get("quantification_gaps", []),
        "weak_phrases": quality_result.get("weak_phrases", []),
        "meets_experience_requirement": experience_result.get("meets_experience_requirement", True),
        "experience_gap_summary": experience_result.get("experience_gap_summary", ""),
    }
    recommendation_result = recommendation_agent.run(rec_context)

    # --- Stage 10: Final Report Agent ---
    matching_skills = skill_match.get("exact_matches", []) + [
        m.get("resume_skill", "") for m in skill_match.get("related_matches", [])
    ]
    missing_skills = skill_match.get("missing_required_skills", [])
    report_context = {
        "candidate_name": (parsed_resume.get("personal_info", {}) or {}).get("name", ""),
        "job_title": job_description.title,
        "overall_score": scores["overall_score"],
        "status": scores["status"],
        "matching_skills": matching_skills,
        "missing_skills": missing_skills,
    }
    final_report = final_report_agent.run(report_context)

    # --- Persist Analysis row ---
    analysis = Analysis(
        user_id=user_id,
        resume_id=resume.id,
        job_description_id=job_description.id,
        ats_score=sub_scores["ats_score"],
        job_match_score=scores["job_match_score"],
        skill_score=skill_score,
        keyword_score=keyword_score,
        experience_score=sub_scores["experience_score"],
        education_score=sub_scores["education_score"],
        resume_quality_score=sub_scores["resume_quality_score"],
        overall_score=scores["overall_score"],
        recommendation=final_report.get("final_summary", ""),
        status=scores["status"],
    )
    db.add(analysis)
    db.flush()  # get analysis.id without committing

    # --- Persist extracted_skills ---
    required_names = {(s.get("name", s) if isinstance(s, dict) else s) for s in required_skills}
    preferred_names = {(s.get("name", s) if isinstance(s, dict) else s) for s in preferred_skills}
    skill_type_map = {}
    for s in required_skills + preferred_skills:
        if isinstance(s, dict):
            skill_type_map[s.get("name")] = s.get("category", "")

    all_skill_names = set(resume_skills) | required_names | preferred_names
    matching_set = set(matching_skills)
    for name in all_skill_names:
        if not name:
            continue
        db.add(ExtractedSkill(
            analysis_id=analysis.id,
            skill_name=name,
            skill_type=skill_type_map.get(name, ""),
            present_in_resume=1 if name in resume_skills or name in matching_set else 0,
            required_by_job=1 if name in required_names else 0,
        ))

    # --- Persist missing_keywords ---
    for kw in keyword_match.get("keyword_status", []):
        if kw.get("status") in ("Missing", "Partially Found"):
            db.add(MissingKeyword(
                analysis_id=analysis.id,
                keyword=kw.get("keyword", ""),
                importance=kw.get("importance", "Medium"),
            ))

    # --- Persist recommendations ---
    for rec in recommendation_result.get("recommendations", []):
        db.add(Recommendation(
            analysis_id=analysis.id,
            category=rec.get("category", "General"),
            recommendation=rec.get("recommendation", ""),
            priority=rec.get("priority", "MEDIUM"),
        ))

    # --- Persist raw agent outputs for auditability ---
    _persist_agent_result(db, analysis.id, "resume_parser_agent", parsed_resume)
    _persist_agent_result(db, analysis.id, "jd_analyzer_agent", jd_analysis)
    _persist_agent_result(db, analysis.id, "ats_agent", ats_result)
    _persist_agent_result(db, analysis.id, "skill_matching_agent", skill_match)
    _persist_agent_result(db, analysis.id, "keyword_agent", keyword_match)
    _persist_agent_result(db, analysis.id, "experience_agent", experience_result)
    _persist_agent_result(db, analysis.id, "resume_quality_agent", quality_result)
    _persist_agent_result(db, analysis.id, "recommendation_agent", recommendation_result)
    _persist_agent_result(db, analysis.id, "final_report_agent", final_report)

    db.commit()
    db.refresh(analysis)

    # Attach transient (non-persisted) rich data used by the API response builder
    analysis._runtime = {
        "matching_skills": matching_skills,
        "missing_skills": missing_skills,
        "missing_preferred_skills": skill_match.get("missing_preferred_skills", []),
        "matching_keywords": [k["keyword"] for k in keyword_match.get("keyword_status", []) if k.get("status") == "Found"],
        "missing_keywords_detail": [k for k in keyword_match.get("keyword_status", []) if k.get("status") != "Found"],
        "ats_issues": ats_result.get("issues", []),
        "strengths": ats_result.get("strengths", []),
        "weaknesses": quality_result.get("grammar_issues", []) + [w["current"] for w in quality_result.get("weak_phrases", [])],
        "recommendations": recommendation_result.get("recommendations", []),
        "final_summary": final_report.get("final_summary", ""),
    }

    return analysis
