import html
import random
import re
import time
import xml.etree.ElementTree as ET
import pandas as pd
import requests

print(">>> Starting RSS EV Review Extractor with Rate-Limit Protection...")

queries = [
    "Nexon EV",
    "Tata EV charging",
    "Punch EV review",
    "Ather 450X experience",
    "Ola electric service",
    "EV charging highway India",
]

# Reddit prefers distinct, custom App identifiers over generic browser headers
custom_headers = [
    {
        "User-Agent": (
            "AcademicDataMining/1.0 (student research; contact:"
            " academic_ev_study)"
        )
    },
    {
        "User-Agent": (
            "Python:IndianEVAnalysis:v1.1 (by /u/ev_researcher_project)"
        )
    },
    {"User-Agent": "EVResearchBot/2.0 (data mining project on charging infra)"},
]

records = []

for q in queries:
  formatted_query = requests.utils.quote(q)
  url = f"https://www.reddit.com/r/CarsIndia/search.rss?q={formatted_query}&restrict_sr=on&sort=relevance"
  print(f"\nFetching RSS feed for '{q}'...")

  success = False
  retries = 3

  while retries > 0 and not success:
    header = random.choice(custom_headers)
    try:
      response = requests.get(url, headers=header, timeout=15)

      if response.status_code == 200:
        root = ET.fromstring(response.content)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entries = root.findall("atom:entry", ns)
        print(f"  -> Successfully parsed {len(entries)} items.")

        for entry in entries:
          title_el = entry.find("atom:title", ns)
          content_el = entry.find("atom:content", ns)
          link_el = entry.find("atom:link", ns)
          updated_el = entry.find("atom:updated", ns)

          raw_title = title_el.text if title_el is not None else ""
          raw_html = content_el.text if content_el is not None else ""
          link = link_el.attrib.get("href", "") if link_el is not None else ""
          date = updated_el.text if updated_el is not None else ""

          clean_text = re.sub(r"<[^>]+>", " ", html.unescape(raw_html))
          clean_text = re.sub(r"\s+", " ", clean_text).strip()
          combined_text = f"{raw_title}. {clean_text}"

          if len(combined_text) > 30:
            records.append({
                "vehicle_topic": q,
                "title": raw_title,
                "review_text": combined_text,
                "date": date,
                "url": link,
            })
        success = True

      elif response.status_code == 429:
        print(
            "  -> Rate limited (429). Backing off for 12 seconds before"
            " retrying..."
        )
        time.sleep(12)
        retries -= 1

      else:
        print(f"  -> Failed with status {response.status_code}")
        break

    except Exception as e:
      print(f"  -> Request error: {e}")
      time.sleep(5)
      retries -= 1

  # Safe wait between distinct queries
  time.sleep(6)

if records:
  df = pd.DataFrame(records).drop_duplicates(subset=["title"])
  output_file = "indian_ev_reviews_dataset.csv"
  df.to_csv(output_file, index=False, encoding="utf-8")
  print(
      f"\nSUCCESS: Added to dataset! Total records saved: {len(df)} in"
      f" '{output_file}'"
  )
else:
  print("\nNo entries extracted.")