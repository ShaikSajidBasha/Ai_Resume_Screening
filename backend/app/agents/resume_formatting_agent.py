from typing import Any, Dict, List


def run(optimized_resume: Dict[str, Any]) -> Dict[str, Any]:
    sections = [
        "Professional Summary",
        "Technical Skills",
        "Education",
        "Experience",
        "Projects",
        "Certifications",
        "Achievements",
    ]
    available = [s for s in sections if optimized_resume.get(s.lower().replace(" ", "_")) or (isinstance(optimized_resume.get("skills"), dict) and optimized_resume["skills"])]
    return {
        "formatting": {
            "layout": "single-column",
            "font": "Arial",
            "margins": "0.5in",
            "section_spacing": "standard",
            "ats_friendly": True,
        },
        "recommended_sections": available or sections,
        "notes": [
            "Use standard section headings.",
            "Keep a single-column layout for ATS compatibility.",
            "Avoid graphics, decorative elements, and image-based text.",
        ],
    }
