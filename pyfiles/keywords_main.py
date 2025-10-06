from onet_api import OnetAPI
from resume_parser import ResumeParser
from keyword_suggester import KeywordSuggester
from resume_scorer import ResumeScorer


def main():
    # --- User input ---
    file_path = input("Upload your resume file path: ").strip("\"'")
    job_title = input("Enter the job title you're targeting: ")

    # --- Parse resume ---
    resume_text = ResumeParser.extract_text(file_path)

    # --- Connect to O*NET ---
    api_username = "carnegie_mellon_univ2"
    api_password = "3893fqi"
    onet = OnetAPI(api_username, api_password)

    # --- Return jobs from O*NET ---
    jobs = onet.search_job(job_title)

    print("\nJobs found:")
    for i, (title, code) in enumerate(jobs, 1):
        print(f"{i}. {title} ({code})")

    #  --- User selects job ---
    choice = int(input("Select the best match (number): "))
    chosen_job = jobs[choice - 1][0]
    chosen_code = jobs[choice - 1][1]

    # --- Get keywords for job ---
    keywords = onet.get_keywords(chosen_code)

    # --- Suggest keywords ---
    missing_keywords = KeywordSuggester.suggest_keywords(resume_text, keywords)
    in_resume = sorted(set(keywords) - set(missing_keywords))

    print("\n Keywords already in your resume:")
    for kw in in_resume:
        print("-", kw)

    print("\n Suggested keywords to add to your resume:")
    for kw in sorted(set(missing_keywords)):
        print("-", kw)

    # --- Score resume ---
    keyword_score, format_score, sections_present = ResumeScorer.score_resume(
        resume_text, keywords)

    print(f"\n Resume Scores:")
    print(f"Keyword coverage: {keyword_score:.1f}%")
    print(f"Formatting score: {format_score:.1f}%\n")

    print("Formatting sections present:")
    for section, present in sections_present.items():
        print(f"- {section.replace('_', ' ').title()}: {'Yes' if present else 'No'}")

    return job_title


if __name__ == "__main__":
    main()
