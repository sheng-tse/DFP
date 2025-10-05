# Levels.fyi Heatmap Scraper & Visualization

## What this does
- Scrapes live salary distribution data from https://www.levels.fyi/heatmap/
- Creates a clean CSV of 130+ regions with p10–p90 salary percentiles
- Automatically generates two PNG charts:
  - Top 20 regions by median compensation
  - Percentile distribution for the top 10 regions

## How to run (step-by-step)

1. Open a terminal in this folder.
2. (Optional but recommended) Create a virtual environment:
   python -m venv .venv
   .venv\Scripts\activate  (Windows)
   source .venv/bin/activate (Mac/Linux)
3. Install dependencies:
   pip install -r requirements.txt
4. Install Playwright browser engine:
   playwright install chromium
5. Run the script:
   python run_all.py

✅ Output files:
- levels_heatmap_regions.csv
- chart_top20_median.png
- chart_percentile_bars.png