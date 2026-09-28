import re
from typing import Any, Dict, List


def _find_text_blocks(text: str, names: List[str]) -> List[str]:
    blocks = []
    for name in names:
        pattern = rf"(?:{re.escape(name)}\s*\n|{re.escape(name)}\s*:)"
        if re.search(pattern, text, re.IGNORECASE):
            blocks.append(name)
    return blocks


def run(original_resume: str, candidate_data: Dict[str, Any]) -> Dict[str, Any]:
    original = original_resume or ""
    candidate = candidate_data or {}
    fabricated = []
    modified_sections = []
    warnings = []

    unsupported_company_terms = ["Google", "Microsoft", "Amazon", "Meta", "Uber", "Apple", "Netflix"]
    unsupported_experience_pattern = r"(?:Senior|Lead|Junior|Software|Data|Machine Learning|Product|Frontend|Backend|Full Stack|QA|DevOps|Analyst|Engineer|Developer|Intern|Manager|Associate)\s*(?:[A-Za-z\-]+\s*){0,5}(?:at|for|with)\s+(?:Google|Microsoft|Amazon|Meta|Uber|Apple|Netflix)"

    def _flag_unsupported(value: str, field_name: str):
        if not value:
            return

        for company in unsupported_company_terms:
            if company.lower() not in value.lower():
                continue

            role_at_company = bool(re.search(
                rf"(?:Senior|Lead|Junior|Software|Data|Machine Learning|Product|Frontend|Backend|Full Stack|QA|DevOps|Analyst|Engineer|Developer|Intern|Manager|Associate)[A-Za-z\-\s]*(?:at|for|with)\s+{re.escape(company)}",
                value,
                re.IGNORECASE,
            ))
            experience_section_claim = bool(re.search(r"Experience\s*\n.*?\b(?:at|for|with)\s+" + re.escape(company), value, re.IGNORECASE | re.DOTALL))
            experience_company_match = bool(re.search(rf"(?:at|for|with)\s+{re.escape(company)}.*?(?:Experience|Worked|Role|Engineer|Developer|Analyst|Manager)", original, re.IGNORECASE | re.DOTALL))

            # A certification mention is not equivalent to work experience.
            if (role_at_company or experience_section_claim) and not experience_company_match:
                fabricated.append(value[:160])
                modified_sections.append(field_name)
                return

    for field in ["professional_summary", "experience", "projects", "education", "certifications", "achievements"]:
        value = candidate.get(field)
        if not value:
            continue
        if isinstance(value, str):
            _flag_unsupported(value, field)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    _flag_unsupported(item, field)

    if not original or len(original) < 20:
        return {"is_valid": False, "fabricated_content": ["Resume content is too short to validate."], "modified_sections": ["resume"], "warnings": ["Original resume content missing."]}

    for required in ["name", "email", "phone"]:
        if required in candidate and candidate[required]:
            if required == "name" and candidate[required] not in original:
                fabricated.append(candidate[required])
                warnings.append("Candidate name cannot be altered without support.")
            if required in {"email", "phone"} and candidate[required] and candidate[required] not in original:
                fabricated.append(candidate[required])
                warnings.append(f"{required.title()} value not supported by the original resume.")

    return {
        "is_valid": not fabricated,
        "fabricated_content": fabricated,
        "modified_sections": sorted(set(modified_sections)),
        "warnings": warnings,
    }
