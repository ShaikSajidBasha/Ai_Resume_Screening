"""
Lightweight, dependency-free rule-based text extraction used ONLY as a
fallback when the Google AI API is unavailable/unconfigured. This keeps the
app usable for local demos even without an API key, per the requirement that
every feature have a working fallback.

Not a replacement for the LLM's semantic understanding — just enough
structure-aware parsing (section headers + a curated skill vocabulary) to
produce a reasonable, non-empty result.
"""
import re

# A reasonably broad vocabulary of common tech/soft skills used for
# keyword-spotting when no LLM is available. Not exhaustive by design.
COMMON_SKILLS = [
    "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "Rust", "PHP", "Ruby",
    "SQL", "MySQL", "PostgreSQL", "MongoDB", "SQLite", "Redis", "Oracle",
    "React", "Angular", "Vue", "Node.js", "Express", "FastAPI", "Django", "Flask", "Spring Boot",
    "HTML", "CSS", "Tailwind CSS", "Bootstrap",
    "AWS", "Azure", "GCP", "Google Cloud", "Docker", "Kubernetes", "Terraform", "CI/CD", "Jenkins",
    "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "Scikit-learn", "NLP",
    "Data Analysis", "Data Visualization", "Power BI", "Tableau", "Excel", "Pandas", "NumPy",
    "Git", "GitHub", "REST APIs", "GraphQL", "Microservices", "Linux", "Agile", "Scrum",
    "Statistics", "MLOps", "Communication", "Teamwork", "Leadership", "Problem Solving",
]

SECTION_HEADER_RE = {
    "skills": re.compile(r"(?im)^\s*(technical\s+)?skills\s*:?\s*$"),
    "required_skills": re.compile(r"(?im)^\s*required\s+skills\s*:?\s*$"),
    "preferred_skills": re.compile(r"(?im)^\s*preferred\s+skills\s*:?\s*$"),
    "education": re.compile(r"(?im)^\s*education\s*:?\s*$"),
    "certifications": re.compile(r"(?im)^\s*certifications?\s*:?\s*$"),
    "experience": re.compile(r"(?im)^\s*(work\s+)?experience\s*:?\s*$"),
}


def extract_known_skills(text: str) -> list:
    """Case-insensitive whole-word/phrase match against COMMON_SKILLS."""
    if not text:
        return []
    found = []
    lower_text = text.lower()
    for skill in COMMON_SKILLS:
        pattern = r"(?<![a-zA-Z0-9])" + re.escape(skill.lower()) + r"(?![a-zA-Z0-9])"
        if re.search(pattern, lower_text):
            found.append(skill)
    return found


def extract_section_lines(text: str, header_key: str, max_lines: int = 15) -> list:
    """Returns non-empty lines following a recognized section header, until the next
    blank-line-separated all-caps header or another known header is hit."""
    header_re = SECTION_HEADER_RE.get(header_key)
    if not header_re:
        return []

    lines = text.splitlines()
    for i, line in enumerate(lines):
        if header_re.match(line.strip()):
            collected = []
            for candidate in lines[i + 1: i + 1 + max_lines]:
                stripped = candidate.strip(" \t-•*")
                if not stripped:
                    if collected:
                        break
                    continue
                if any(h.match(stripped) for h in SECTION_HEADER_RE.values()):
                    break
                if stripped.isupper() and len(stripped.split()) <= 4:
                    break
                collected.append(stripped)
            return collected
    return []


def extract_required_years(text: str) -> int:
    match = re.search(r"(\d{1,2})\s*\+?\s*years?", text, re.IGNORECASE)
    return int(match.group(1)) if match else 0
