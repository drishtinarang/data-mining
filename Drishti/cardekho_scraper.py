"""
CarDekho EV Review Scraper
===========================
Scrapes user reviews for one or more EV models from CarDekho's
"user-reviews" pages, e.g.:
    https://www.cardekho.com/tata/nexon-ev/user-reviews/1
    https://www.cardekho.com/tata/nexon-ev/user-reviews/2
    ...

Each review on the page follows this visible pattern:
    <reviewer name> on <Month Day, Year><rating>
    <Review Title>
    <Review body text>...Read More

This script:
  1. Fetches each page of a model's review listing
  2. Extracts reviewer, date, rating, title, and review text using regex
     over the page's visible text (robust to minor markup changes)
  3. Auto-detects total page count from "Page X of Y pages"
  4. Saves everything to a single CSV

--------------------------------------------------------------------
SETUP (run once)
--------------------------------------------------------------------
pip install requests beautifulsoup4 pandas --break-system-packages

--------------------------------------------------------------------
HOW TO RUN
--------------------------------------------------------------------
python cardekho_scraper.py

By default it scrapes the Tata Nexon EV. To scrape a different model,
edit the MODEL_SLUG variable below — find the slug from the model's
CarDekho URL, e.g. for "https://www.cardekho.com/mg/zs-ev/user-reviews"
the slug is "mg/zs-ev".

Output: data/cardekho_<model>_reviews.csv
"""

import os
import re
import time
import random
import requests
from bs4 import BeautifulSoup

# ----------------------------------------------------------------
# CONFIG — change this to scrape a different model
# ----------------------------------------------------------------
MODEL_SLUG = "tata/nexon-ev"   # e.g. "mg/zs-ev", "tata/tiago-ev", "tata/punch-ev"
MAX_PAGES = None               # None = auto-detect from the page; or set an int to cap it

BASE_URL = f"https://www.cardekho.com/{MODEL_SLUG}/user-reviews"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 "
        "(research project; contact: your_email@example.com)"
    )
}
OUTPUT_DIR = "data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Regex to pull "<name> on <Month DD, YYYY><rating>" e.g. "aravind on Dec 07, 20234"
# The rating (e.g. "4") is glued directly onto the year with no space.
REVIEW_HEADER_RE = re.compile(
    r"([a-zA-Z][a-zA-Z .]{1,40}) on ([A-Z][a-z]{2} \d{1,2}, \d{4})(\d(?:\.\d)?)?"
)
TOTAL_PAGES_RE = re.compile(r"Page\s+\d+\s+of\s+(\d+)\s+pages")


def get_total_pages(soup_text):
    match = TOTAL_PAGES_RE.search(soup_text)
    return int(match.group(1)) if match else 1


def parse_reviews_from_page(html):
    """Extract review entries from one CarDekho review-listing page."""
    soup = BeautifulSoup(html, "html.parser")
    page_text = soup.get_text("\n", strip=True)

    reviews = []
    matches = list(REVIEW_HEADER_RE.finditer(page_text))

    for i, m in enumerate(matches):
        reviewer, date, rating = m.groups()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else start + 600
        chunk = page_text[start:end].strip()

        # chunk now looks like: "<Title>\n<Review body...Read More>"
        lines = [l for l in chunk.split("\n") if l.strip()]
        title = lines[0] if lines else ""
        body = " ".join(lines[1:]) if len(lines) > 1 else ""
        body = body.replace("Read More", "").strip()

        # Skip obvious false positives (too short / not real review content)
        if len(title) < 3 and len(body) < 10:
            continue

        reviews.append({
            "reviewer": reviewer.strip(),
            "date": date.strip(),
            "rating": rating.strip() if rating else "",
            "title": title.strip(),
            "review_text": body,
        })

    return reviews


def scrape_model(model_slug):
    all_reviews = []
    page = 1
    total_pages = MAX_PAGES or 1

    while page <= total_pages:
        url = f"{BASE_URL}/{page}"
        print(f"Fetching page {page}: {url}")
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            print(f"  ! failed to fetch page {page}: {e}")
            break

        if page == 1 and MAX_PAGES is None:
            total_pages = get_total_pages(resp.text)
            print(f"Detected {total_pages} total pages of reviews.")

        page_reviews = parse_reviews_from_page(resp.text)
        print(f"  -> extracted {len(page_reviews)} reviews")
        all_reviews.extend(page_reviews)

        page += 1
        time.sleep(random.uniform(2, 4))  # polite delay — don't hammer the server

    return all_reviews


if __name__ == "__main__":
    model_name_for_file = MODEL_SLUG.replace("/", "_")
    reviews = scrape_model(MODEL_SLUG)

    out_path = os.path.join(OUTPUT_DIR, f"cardekho_{model_name_for_file}_reviews.csv")

    import csv
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["reviewer", "date", "rating", "title", "review_text"])
        writer.writeheader()
        writer.writerows(reviews)

    print(f"\nDone. Saved {len(reviews)} reviews -> {out_path}")
