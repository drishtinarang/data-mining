import re
import time
from bs4 import BeautifulSoup
import pandas as pd
import requests


def scrape_carwale_ev_reviews(
    model_slug="tata-cars/nexon-ev", max_pages=5, delay_sec=2
):
  """Scrapes user reviews from CarWale for a given vehicle model slug.

  Args:
      model_slug (str): URL slug of the car (e.g. 'tata-cars/nexon-ev',
        'mg-cars/zs-ev') max_pages (int): Number of pagination pages to scrape
        delay_sec (int): Pause between requests to prevent rate-limiting

  Returns:
      pd.DataFrame: Cleaned reviews with title, reviewer info, text, and date
  """
  base_url = f"https://www.carwale.com/{model_slug}/reviews/"
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
          " like Gecko) Chrome/120.0.0.0 Safari/537.36"
      ),
      "Accept-Language": "en-US,en;q=0.9",
  }

  all_reviews = []

  for page in range(1, max_pages + 1):
    page_url = base_url if page == 1 else f"{base_url}page/{page}/"
    print(f"Fetching page {page}: {page_url}")

    try:
      response = requests.get(page_url, headers=headers, timeout=10)
      if response.status_code != 200:
        print(f"Failed to fetch page {page}. Status: {response.status_code}")
        break

      soup = BeautifulSoup(response.text, "html.parser")

      # Review blocks on CarWale typically contain an h3 title and body text
      review_containers = soup.find_all(
          ["div", "li"], class_=re.compile(r"review|card", re.I)
      )

      # Fallback selector targeting headings if classes change dynamically
      headings = soup.find_all("h3")

      for h3 in headings:
        title = h3.get_text(strip=True)
        # Filter out navigation or irrelevant headings
        if not title or len(title) < 4:
          continue

        parent = h3.find_parent(["div", "li"])
        if not parent:
          continue

        # Extract review body
        paragraphs = parent.find_all("p")
        body_parts = [
            p.get_text(strip=True)
            for p in paragraphs
            if len(p.get_text(strip=True)) > 25
        ]
        review_text = " ".join(body_parts)

        # Extract meta (date/author/rating) if available in parent
        meta_text = parent.get_text(" ", strip=True)
        date_match = re.search(
            r"(\d+\s+(?:days?|months?|years?)\s+ago)", meta_text
        )
        posted_date = date_match.group(1) if date_match else "Unknown"

        if review_text:
          all_reviews.append({
              "vehicle_model": model_slug.split("/")[-1],
              "review_title": title,
              "review_text": review_text,
              "time_frame": posted_date,
          })

      time.sleep(delay_sec)

    except Exception as e:
      print(f"Error on page {page}: {e}")
      break

  # Deduplicate identical extracted blocks
  df = pd.DataFrame(all_reviews).drop_duplicates(subset=["review_title"])
  return df


if __name__ == "__main__":
  # Models to mine for Indian market EV analysis
  ev_models = [
      "tata-cars/nexon-ev",
      "tata-cars/punch-ev",
      "mg-cars/zs-ev",
  ]

  combined_dfs = []
  for model in ev_models:
    print(f"\n--- Mining reviews for {model} ---")
    df_model = scrape_carwale_ev_reviews(model_slug=model, max_pages=3)
    combined_dfs.append(df_model)

  final_df = pd.concat(combined_dfs, ignore_index=True)
  output_filename = "indian_ev_customer_reviews.csv"
  final_df.to_csv(output_filename, index=False)
  print(
      f"\nExtraction complete! Saved {len(final_df)} reviews to"
      f" {output_filename}."
  )