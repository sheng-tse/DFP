import re
from typing import Tuple, List

class ResumeScorer:
    @staticmethod
    def score_resume(resume_text: str, keywords: List[str]) -> Tuple[float, float, dict]:
        """
        Score a resume based on:
        1. Keyword coverage
        2. Formatting sections present

        Returns:
        - keyword_score: percentage of keywords present
        - format_score: percentage of key sections present
        - sections_present: dict of section_name -> True/False
        """
        # --- Keywords ---
        resume_lower = resume_text.lower()
        keywords_lower = [kw.lower() for kw in keywords]
        keywords_found = sum(1 for kw in keywords_lower if re.search(rf"\b{re.escape(kw)}\b", resume_lower))
        keyword_score = (keywords_found / len(keywords)) * 100 if keywords else 0

        # --- Formatting sections ---
        sections_present = {
            "contact_info": bool(re.search(r"\b\d{3}[-\s.]?\d{3}[-\s.]?\d{4}\b", resume_text) or re.search(r"@", resume_text)),
            "education": bool(re.search(r"\beducation\b", resume_lower)),
            "skills": bool(re.search(r"\bskills\b", resume_lower)),
            "experience": bool(re.search(r"\b(professional )?experience\b", resume_lower)),
            "projects": bool(re.search(r"\bprojects\b", resume_lower)),
        }
        format_score = (sum(sections_present.values()) / len(sections_present)) * 100

        return keyword_score, format_score, sections_present
