import requests
import nltk
from nltk.corpus import stopwords
import spacy
from spacy.lang.en.stop_words import STOP_WORDS
import re

class OnetAPI:
    def __init__(self, api_username: str, api_password: str):
        # Base URL for occupation data
        self.base_url = "https://services.onetcenter.org/v1.9/ws/online/occupations/"
        self.session = requests.Session()
        self.session.auth = (api_username, api_password)

        # Used for cleaning keywords list
        self.nlp = spacy.load("en_core_web_sm")
        self.stop_words = set(stopwords.words('english')) | {
            "work", "accepted", "access", "address", "application", 
            "enforce", "ensuring", "needs", "other", "pen", "related", 
            "requirements", "use", "user", "end", "loss"
        }
        

    def search_job(self, job_title: str):
        # Search for occupation based off of user input keyword
        url = "https://services.onetcenter.org/ws/online/search"
        params = {"keyword": job_title}
        headers = {"Accept": "application/json"}
        response = self.session.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()

        results = []
        
        while True:
            # Extract first 40 occupations based off relevance
            occupations = data.get("occupation", [])
            for occ in occupations:
                title = occ.get("title")
                code = occ.get("code")
                results.append((title, code))

            # Follow the "next" link if present
            next_url = None
            for link in data.get("link", []):
                if link.get("rel") == "next":
                    next_url = link.get("href")
                    break
            
            if not next_url:
                break

            response = self.session.get(next_url, headers=headers)
            response.raise_for_status()
            data = response.json()   
        
        seen = set()     
        unique_results = []
        for item in results:
            if item not in seen:
                seen.add(item)
                unique_results.append(item)

        return unique_results[:40] 

    def get_keywords(self, onet_code: str):
        # Get keywords for a given O*NET occupation code
        headers = {"Accept": "application/json"}
        details_url = f"{self.base_url}{onet_code}/details/"
        response = self.session.get(details_url, headers=headers)

        if response.status_code != 200:
            print(f"Error fetching data for O*NET code {onet_code}: {response.status_code}")
            return []

        data = response.json()
        keywords = set()  # use a set to avoid duplicates

        # 2. Tasks
        if 'tasks' in data and 'task' in data['tasks']:
            for t in data['tasks']['task']:
                for word in t['statement'].replace('.', '').replace(',', '').split():
                    keywords.add(word)

        # 3. Detailed Work Activities
        if 'detailed_work_activities' in data and 'activity' in data['detailed_work_activities']:
            for act in data['detailed_work_activities']['activity']:
                for word in act['name'].replace('.', '').replace(',', '').split():
                    keywords.add(word)

        # 4. Technology Skills
        if 'technology_skills' in data and 'category' in data['technology_skills']:
            for cat in data['technology_skills']['category']:
                if 'title' in cat and 'name' in cat['title']:
                    for word in cat['title']['name'].replace('.', '').replace(',', '').split():
                        keywords.add(word)
                if 'example' in cat:
                    for ex in cat['example']:
                        keywords.add(ex['name'])

        # 5. Interests
        if 'interests' in data and 'element' in data['interests']:
            for e in data['interests']['element']:
                keywords.add(e['name'])

        # 6. Tools & Technology (extra)
        if 'tools_technology' in data and 'technology' in data['tools_technology']:
            if 'category' in data['tools_technology']['technology']:
                for cat in data['tools_technology']['technology']['category']:
                    if 'title' in cat and 'name' in cat['title']:
                        for word in cat['title']['name'].replace('.', '').replace(',', '').split():
                            keywords.add(word)
                    if 'example' in cat:
                        for ex in cat['example']:
                            keywords.add(ex['name'])

        # Clean keywords
        cleaned = set()
        for kw in keywords:
            kw_lower = kw.lower().strip()
            if kw_lower in self.stop_words or kw_lower in STOP_WORDS:
                continue
            doc = self.nlp(kw_lower)
            lemma_kw = [token.lemma_ for token in doc if token.pos_ in {"NOUN", "PROPN", "VERB"}]
            if lemma_kw:
                cleaned.add(' '.join(lemma_kw))
        return sorted(cleaned)
