from PyPDF2 import PdfReader

class ResumeParser:
    @staticmethod
    def extract_text(file_path: str) -> str:
        """Extract raw text from a PDF resume."""
        text = ""
        reader = PdfReader(file_path)
        for page in reader.pages:
            text += page.extract_text() or ""
        return text