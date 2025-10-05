import re
from typing import List

class KeywordSuggester:
    @staticmethod
    def suggest_keywords(resume_text: str, skills: List[str]) -> List[str]:
        """Return keywords from skills not found in resume text."""
        resume_text_lower = resume_text.lower()
        missing = []
        for skill in skills:
            if re.search(rf"\b{re.escape(skill.lower())}\b", resume_text_lower) is None:
                missing.append(skill)
        return missing
