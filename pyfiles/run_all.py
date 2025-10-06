# run_all.py — scrape Levels.fyi heatmap → CSV → charts (self-contained)
# Usage:  python run_all.py
# Outputs:
#   - levels_heatmap_regions.csv
#   - chart_top20_median.png
#   - chart_percentile_bars.png
#   - debug_dump/ (only for troubleshooting)

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

# ----------------- CONFIG -----------------
HEATMAP_URL = "https://www.levels.fyi/heatmap/"
OUTPUT_CSV = "levels_heatmap_regions.csv"
DEBUG_DIR = Path("debug_dump")
DEBUG_DIR.mkdir(exist_ok=True)

# -------------- UTILITIES -----------------


def looks_like_regions_dict(obj: Any) -> bool:
    """
    Heuristic: a big dict whose values are dicts containing
    p10..p90 and primary_name/secondary_name (the DMA table).
    """
    if not isinstance(obj, dict) or not obj:
        return False
    sample_values = list(obj.values())[:10]
    good = 0
    for v in sample_values:
        if not isinstance(v, dict):
            continue
        keys = set(v.keys())
        pct_keys = {"p10", "p25", "p50", "p75", "p90"}
        name_keys = {"primary_name", "secondary_name"}
        if pct_keys.issubset(keys) and (name_keys & keys):
            good += 1
    return good >= max(1, len(sample_values) // 3)


def parse_regions_from_dict(d: Dict) -> pd.DataFrame:
    rows = []
    for region_id, v in d.items():
        if not isinstance(v, dict):
            continue
        rows.append({
            "region_id": region_id,
            "region_name": v.get("primary_name"),
            "detailed_location": v.get("secondary_name"),
            "rank": v.get("rank"),
            "p10": v.get("p10"),
            "p25": v.get("p25"),
            "p50": v.get("p50"),
            "p75": v.get("p75"),
            "p90": v.get("p90"),
            "normalizedMedian": v.get("normalizedMedianSalary"),
            "url": v.get("url"),
        })
    df = pd.DataFrame(rows)
    # Keep only rows that have a name and p50
    df = df[df["region_name"].notna() & df["p50"].notna()]
    if "rank" in df.columns:
        df = df.sort_values("rank", na_position="last")
    return df


def try_live_scrape() -> Optional[pd.DataFrame]:
    """
    Use Playwright to open the page, capture every JSON response,
    find the DMA dict, and parse it. Also dumps JSON to debug_dump.
    """
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return None

    payloads: List[Dict] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context()
        page = ctx.new_page()

        def on_response(resp):
            try:
                ct = (resp.headers or {}).get("content-type", "")
                if "application/json" in ct or resp.url.endswith(".json"):
                    data = resp.json()
                    # dump a few json files for debugging
                    idx = len(list(DEBUG_DIR.glob("json_*.json"))) + 1
                    (DEBUG_DIR / f"json_{idx:03d}.json").write_text(
                        json.dumps(data)[:800000], encoding="utf-8"
                    )
                    payloads.append(data)
            except Exception:
                pass

        page.on("response", on_response)
        page.goto(HEATMAP_URL)
        # allow the app to finish booting & XHRs to fire
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3500)
        html = page.content()
        (DEBUG_DIR / "playwright_final.html").write_text(html, encoding="utf-8")

        # Also try __NEXT_DATA__ from the DOM
        try:
            nd = page.evaluate("() => window.__NEXT_DATA__")
            if isinstance(nd, dict):
                (DEBUG_DIR / "next_data.json").write_text(
                    json.dumps(nd)[:800000], encoding="utf-8"
                )
                payloads.insert(0, nd)
        except Exception:
            pass

        browser.close()

    # Search all captured payloads for the regions dict
    for p in payloads:
        # 1) direct dict with region entries
        if looks_like_regions_dict(p):
            return parse_regions_from_dict(p)
        # 2) search within nested structures
        stack = [p]
        while stack:
            cur = stack.pop()
            if isinstance(cur, dict):
                if looks_like_regions_dict(cur):
                    return parse_regions_from_dict(cur)
                stack.extend(cur.values())
            elif isinstance(cur, list):
                stack.extend(cur)

    return None


def try_from_debug_dump() -> Optional[pd.DataFrame]:
    """
    Fallback: read any json_*.json previously captured in debug_dump/
    and parse the first one that matches the regions dict heuristic.
    """
    json_files = sorted(DEBUG_DIR.glob("json_*.json"))
    for jf in json_files:
        try:
            obj = json.loads(jf.read_text(encoding="utf-8"))
        except Exception:
            continue
        if looks_like_regions_dict(obj):
            return parse_regions_from_dict(obj)
        # nested scan
        stack = [obj]
        while stack:
            cur = stack.pop()
            if isinstance(cur, dict):
                if looks_like_regions_dict(cur):
                    return parse_regions_from_dict(cur)
                stack.extend(cur.values())
            elif isinstance(cur, list):
                stack.extend(cur)
    return None


def save_charts(df: pd.DataFrame) -> None:
    """
    Create two PNG charts with matplotlib:
      1) Top-20 regions by median (p50)
      2) Percentile bars for top-10 by median
    """
    import matplotlib.pyplot as plt

    # ---- 1) Top-20 by median ----
    top20 = df.sort_values("p50", ascending=False).head(20)
    plt.figure(figsize=(11, 8))
    plt.barh(top20["region_name"], top20["p50"])
    plt.gca().invert_yaxis()
    plt.xlabel("Median (p50) Total Comp")
    plt.title("Top 20 Markets by Median Software Engineer Compensation")
    plt.tight_layout()
    plt.savefig("chart_top20_median.png", dpi=200)
    plt.close()

    # ---- 2) Percentile bars for top-10 ----
    top10 = df.sort_values("p50", ascending=False).head(10).copy()
    # Build wide-to-long for stacked bars
    long = top10.melt(
        id_vars=["region_name"],
        value_vars=["p10", "p25", "p50", "p75", "p90"],
        var_name="percentile",
        value_name="comp"
    )
    # Order regions by median descending
    order = top10["region_name"].tolist()
    long["region_name"] = pd.Categorical(
        long["region_name"], categories=order, ordered=True)
    long = long.sort_values(["region_name", "percentile"])

    # Plot grouped bars
    plt.figure(figsize=(12, 8))
    # group by region, plot each percentile cluster
    percentiles = ["p10", "p25", "p50", "p75", "p90"]
    x = range(len(order))
    width = 0.15
    for i, p in enumerate(percentiles):
        series = long[long["percentile"] == p].sort_values("region_name")[
            "comp"].values
        xs = [xi + (i - 2)*width for xi in x]
        plt.bar(xs, series, width=width, label=p)
    plt.xticks(x, order, rotation=30, ha="right")
    plt.ylabel("Compensation")
    plt.title("Percentiles by Region (Top 10 by Median)")
    plt.legend(title="Percentile")
    plt.tight_layout()
    plt.savefig("chart_percentile_bars.png", dpi=200)
    plt.close()


def main():
    # 1) Try live scrape
    df = try_live_scrape()
    if df is None or df.empty:
        print("Live scrape did not yield data. Trying fallback from debug_dump/ ...")

        # 2) Fallback to any json_*.json in debug_dump
        df = try_from_debug_dump()

    if df is None or df.empty:
        print("ERROR: Could not obtain region data from live site or debug_dump/.")
        sys.exit(2)

    # Clean up columns & save CSV
    keep = ["region_id", "region_name", "detailed_location", "rank",
            "p10", "p25", "p50", "p75", "p90", "normalizedMedian", "url"]
    for col in keep:
        if col not in df.columns:
            df[col] = None
    df = df[keep]
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"✅ Saved {len(df)} rows → {OUTPUT_CSV}")

    # 3) Make charts
    try:
        save_charts(df)
        print("✅ Saved charts:")
        print(" - chart_top20_median.png")
        print(" - chart_percentile_bars.png")
    except Exception as e:
        print("Charts step skipped due to error:", e)


if __name__ == "__main__":
    main()
