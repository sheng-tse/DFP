import requests
import re
import json
import matplotlib.pyplot as plt


class LevelsFyiScraper:
    def __init__(self, role: str, location: str = "san-francisco-bay-area"):
        self.role = self.title_to_slug(role)
        self.location = location
        self.url = self.build_url()
        self.json_data = None
        self.histogram = None

    @staticmethod
    def format_location(location_str: str) -> str:
        """Format location slug into human-readable text."""
        return " ".join(word.capitalize() for word in location_str.split('-'))

    @staticmethod
    def title_to_slug(title: str) -> str:
        """Convert job title to a URL-friendly slug."""
        title = title.strip()
        title = re.sub(r'[ /_]+', '-', title)
        return title.lower()

    def build_url(self) -> str:
        """Construct Levels.fyi job compensation URL."""
        if self.location.strip():
            return f"https://www.levels.fyi/t/{self.role}/locations/{self.location}"
        return f"https://www.levels.fyi/t/{self.role}"

    def fetch_page(self):
        """Fetch the webpage and extract JSON payload."""
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(self.url, headers=headers)

        # Extract all <script> blocks
        scripts = re.findall(r"<script[^>]*>(.*?)</script>", res.text, flags=re.DOTALL)
        last_script = scripts[-1].strip()

        try:
            json_start = last_script.index('{')
            self.json_data = json.loads(last_script[json_start:])
        except Exception as e:
            raise ValueError(f"Error parsing JSON: {e}")

    @staticmethod
    def find_key(d, key):
        """Recursive search for a key inside nested JSON."""
        if isinstance(d, dict):
            if key in d:
                return d[key]
            for v in d.values():
                result = LevelsFyiScraper.find_key(v, key)
                if result is not None:
                    return result
        elif isinstance(d, list):
            for item in d:
                result = LevelsFyiScraper.find_key(item, key)
                if result is not None:
                    return result
        return None

    def extract_histogram(self):
        """Extract the jobFamilyHistogram data from JSON."""
        if not self.json_data:
            raise ValueError("No JSON data found. Run fetch_page() first.")
        self.histogram = self.find_key(self.json_data, "jobFamilyHistogram")
        return self.histogram

    def plot_histogram(self):
        """Plot job compensation histograms (base, total comp, bonus, stock)."""
        if not self.histogram:
            raise ValueError("No histogram data found. Run extract_histogram() first.")

        # Extract values
        base_salary = self.histogram.get("baseSalary", {})
        total_comp = self.histogram.get("totalCompensation", {})
        bonus = self.histogram.get("bonus", {})
        stock = self.histogram.get("stockGrant", {})

        # Create subplots
        fig, axs = plt.subplots(2, 2, figsize=(14, 10))

        axs[0, 0].bar(base_salary.keys(), base_salary.values(), color='skyblue')
        axs[0, 0].set_title('Base Salary Percentiles')
        axs[0, 0].set_ylabel('USD')

        axs[0, 1].bar(total_comp.keys(), total_comp.values(), color='lightgreen')
        axs[0, 1].set_title('Total Compensation Percentiles')
        axs[0, 1].set_ylabel('USD')

        axs[1, 0].bar(bonus.keys(), bonus.values(), color='salmon')
        axs[1, 0].set_title('Bonus Percentiles')
        axs[1, 0].set_ylabel('USD')

        axs[1, 1].bar(stock.keys(), stock.values(), color='plum')
        axs[1, 1].set_title('Stock Grant Percentiles')
        axs[1, 1].set_ylabel('USD')

        plt.suptitle(
            f"Job Family Histogram for {self.histogram.get('jobFamily', '')} "
            f"in {self.format_location(self.location)}",
            fontsize=16
        )
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        plt.show()


# ==========================
# Example usage
# ==========================
if __name__ == "__main__":
    scraper = LevelsFyiScraper(role="Data Scientist", location="san-francisco-bay-area")
    scraper.fetch_page()
    histogram = scraper.extract_histogram()

    if histogram:
        print(f"📊 Job Family Histogram for {scraper.role} in {scraper.location}:")
        print(json.dumps(histogram, indent=4))
        scraper.plot_histogram()
    else:
        print(f"⚠️ jobFamilyHistogram not found for {scraper.role} in {scraper.location}")
