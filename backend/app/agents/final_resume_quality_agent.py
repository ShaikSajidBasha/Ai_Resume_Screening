from typing import Any, Dict, List


def run(resume_text: str, optimization_data: Dict[str, Any]) -> Dict[str, Any]:
    quality_score = 90
    issues: List[str] = []
    recommendations: List[str] = []

    if not resume_text or len(resume_text.strip()) < 80:
        quality_score -= 25
        issues.append("Resume content is too short for a professional document.")

    if "Professional Summary" not in resume_text:
        quality_score -= 10
        issues.append("Professional summary section is missing.")

    if "Technical Skills" not in resume_text:
        quality_score -= 5
        issues.append("Technical skills section should be present.")

    if "Email:" in resume_text and "@" not in resume_text:
        quality_score -= 10
        issues.append("Contact information may be incomplete.")

    if quality_score < 70:
        recommendations.append("Review the resume for section completeness and factual consistency.")
        ready = False
    else:
        recommendations.append("Resume is ready for download.")
        ready = True

    return {
        "quality_score": max(0, min(100, quality_score)),
        "ats_compatibility": max(0, min(100, quality_score)),
        "issues": issues,
        "final_recommendations": recommendations,
        "ready_for_download": ready,
    }
