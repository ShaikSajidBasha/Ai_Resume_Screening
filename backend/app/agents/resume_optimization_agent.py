import re
from typing import Any, Dict, List


def _extract_name(resume_text: str) -> str:
    match = re.search(r"^\s*([A-Z][A-Za-z'\-.]+(?:\s+[A-Z][A-Za-z'\-.]+){0,3})", resume_text, re.MULTILINE)
    return match.group(1).strip() if match else "Candidate"


def _extract_contact(resume_text: str) -> Dict[str, str]:
    email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", resume_text)
    phone_match = re.search(r"(?:\+?\d[\d\s().-]{7,}\d)", resume_text)
    return {
        "name": _extract_name(resume_text),
        "email": email_match.group(0) if email_match else "",
        "phone": phone_match.group(0).strip() if phone_match else "",
    }


def _skill_bucket(terms: List[str]) -> Dict[str, List[str]]:
    buckets = {
        "Programming Languages": [],
        "Frameworks": [],
        "Databases": [],
        "AI/ML": [],
        "Tools": [],
        "Cloud": [],
        "Other Technical Skills": [],
    }
    normalized = {s.strip() for s in terms if s and s.strip()}

    for skill in sorted(normalized):
        key = skill.lower()
        if key in {"python", "java", "c++", "c", "javascript", "sql", "html", "css", "typescript", "r", "scala", "go", "php", "swift", "kotlin"}:
            buckets["Programming Languages"].append(skill)
        elif key in {"react", "fastapi", "django", "flask", "spring", "node.js", "express", "pandas", "numpy", "scikit-learn", "pytorch", "tensorflow", "opencv", "selenium"}:
            buckets["Frameworks"].append(skill)
        elif key in {"mysql", "postgresql", "mongodb", "sqlite", "redis", "oracle", "sql server"}:
            buckets["Databases"].append(skill)
        elif key in {"machine learning", "deep learning", "data analysis", "nlp", "computer vision", "ai", "ml", "statistics", "data mining"}:
            buckets["AI/ML"].append(skill)
        elif key in {"git", "github", "docker", "kubernetes", "jira", "tableau", "power bi", "excel", "aws", "azure", "gcp", "linux", "vscode", "postman"}:
            buckets["Tools"].append(skill)
        elif key in {"aws", "azure", "gcp", "docker", "kubernetes"}:
            buckets["Cloud"].append(skill)
        else:
            buckets["Other Technical Skills"].append(skill)

    return {k: sorted(set(v)) for k, v in buckets.items() if v}


def _clean_skill_list(skills: List[str]) -> List[str]:
    out = []
    seen = set()
    for s in skills:
        cleaned = s.strip()
        if cleaned and cleaned.lower() not in seen:
            out.append(cleaned)
            seen.add(cleaned.lower())
    return out

def _extract_sections(resume_text: str) -> Dict[str, str]:
    heading_aliases = {
        "summary": "summary",
        "professional summary": "summary",
        "skills": "skills",
        "technical skills": "skills",
        "core competencies": "skills",
        "tools": "skills",
        "education": "education",
        "academic details": "education",
        "experience": "experience",
        "work experience": "experience",
        "internships": "experience",
        "projects": "projects",
        "certifications": "certifications",
        "certificates": "certifications",
        "achievements": "achievements",
        "languages": "languages",
    }
    sections: Dict[str, List[str]] = {}
    current_section = None

    for line in resume_text.splitlines():
        heading = re.sub(r"^\s*#+\s*|\s*#+\s*$", "", line).strip().rstrip(":").strip().lower()
        if heading in heading_aliases:
            current_section = heading_aliases[heading]
            sections.setdefault(current_section, [])
        elif current_section:
            sections[current_section].append(line)

    result = {}
    for section, lines in sections.items():
        unique_lines = []
        seen_lines = set()
        for line in lines:
            normalized = re.sub(r"\s+", " ", line).strip().casefold()
            if normalized and normalized not in seen_lines:
                unique_lines.append(line)
                seen_lines.add(normalized)
        result[section] = "\n".join(unique_lines).strip()
    return result


def run(original_resume: str, job_description: str, analysis_data: Dict[str, Any], recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
    original = original_resume or ""
    sections = _extract_sections(original)
    contact = _extract_contact(original)

    summary = sections.get("summary", "")
    if not summary:
        summary_bits = []
        if any(degree in original for degree in ("B.Tech", "Bachelor", "Master", "Degree")):
            summary_bits.append("Graduate with a strong technical foundation")
        if any(skill in original.lower() for skill in ("python", "sql", "machine learning")):
            summary_bits.append("focused on software development and data-driven problem solving")
        summary = ". ".join(summary_bits)

    raw_skills = []
    for item in re.split(r"[,\n•]", sections.get("skills", "")):
        cleaned_item = item.strip()
        if ":" in cleaned_item:
            cleaned_item = cleaned_item.split(":", 1)[1].strip()
        if cleaned_item:
            raw_skills.append(cleaned_item)
    skills = _skill_bucket(_clean_skill_list(raw_skills))

    experience_section = sections.get("experience", "")
    project_section = sections.get("projects", "")
    projects = [{
        "title": "Project",
        "description": re.sub(r"\s+", " ", project_section).strip(),
    }] if project_section else []
    education = sections.get("education", "")
    certifications = sections.get("certifications", "")
    achievements = [sections["achievements"]] if sections.get("achievements") else []

    result = {
        "name": contact["name"],
        "email": contact["email"],
        "phone": contact["phone"],
        "professional_summary": summary,
        "skills": skills,
        "experience": experience_section,
        "projects": projects,
        "education": education,
        "certifications": certifications,
        "achievements": achievements,
        "optimized_text": "",
        "warnings": [],
    }

    text_parts = [contact["name"]]
    if contact["email"] or contact["phone"]:
        text_parts.append(f"Email: {contact['email']} | Phone: {contact['phone']}")
    if summary:
        text_parts.extend(["", "Professional Summary", summary])
    if skills:
        text_parts.extend(["", "Technical Skills"])
        text_parts.extend(f"{name}: {', '.join(items)}" for name, items in skills.items())
    for heading, content in (
        ("Education", education),
        ("Experience", experience_section),
    ):
        if content:
            text_parts.extend(["", heading, content])
    if projects:
        text_parts.extend(["", "Projects"])
        text_parts.extend(f"- {project['description']}" for project in projects)
    if certifications:
        text_parts.extend(["", "Certifications", certifications])
    if achievements:
        text_parts.extend(["", "Achievements", *[f"- {item}" for item in achievements]])
    if sections.get("languages"):
        text_parts.extend(["", "Languages", sections["languages"]])

    result["optimized_text"] = "\n".join(text_parts)
    result["job_relevance_notes"] = [
        item.get("recommendation", "") for item in recommendations if isinstance(item, dict)
    ]
    return result
