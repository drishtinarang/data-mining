import time
from bs4 import BeautifulSoup
from curl_cffi import requests
import pandas as pd

print(">>> Starting Team-BHP Deep Scraper for EV Reviews & Charging Posts...")

base_forum_url = "https://www.team-bhp.com/forum/electric-cars/"
headers = {"Accept-Language": "en-US,en;q=0.9"}

thread_links = []
max_index_pages = 3  # Scrapes first 3 pages of the forum listing

# Step 1: Collect thread URLs across index pages
for page_num in range(1, max_index_pages + 1):
  index_url = (
      base_forum_url
      if page_num == 1
      else f"{base_forum_url}index{page_num}.html"
  )
  print(f"Collecting threads from index page {page_num}: {index_url}")

  try:
    res = requests.get(
        index_url, impersonate="chrome120", timeout=20, headers=headers
    )
    if res.status_code == 200:
      soup = BeautifulSoup(res.text, "html.parser")
      tags = soup.find_all(
          "a", id=lambda x: x and x.startswith("thread_title_")
      )

      for tag in tags:
        title = tag.get_text(strip=True)
        link = tag.get("href", "")
        if not link.startswith("http"):
          link = f"https://www.team-bhp.com/forum/electric-cars/{link}"

        # Focus on reviews, real-world ownership, range, and charging
        thread_links.append({"title": title, "url": link})

    time.sleep(1.5)
  except Exception as e:
    print(f"Error fetching index page {page_num}: {e}")

print(f"\nFound {len(thread_links)} total threads to mine.")

# Step 2: Visit each thread and extract user comments/reviews
all_posts_data = []

# Scrape posts from the first 15 relevant threads (adjust as needed)
target_threads = thread_links[:15]

for idx, item in enumerate(target_threads, 1):
  print(f"[{idx}/{len(target_threads)}] Mining: {item['title'][:55]}...")

  try:
    res = requests.get(
        item["url"], impersonate="chrome120", timeout=20, headers=headers
    )
    if res.status_code == 200:
      thread_soup = BeautifulSoup(res.text, "html.parser")

      # Team-BHP post text containers typically reside in div id="post_message_*"
      post_divs = thread_soup.find_all(
          "div", id=lambda x: x and x.startswith("post_message_")
      )

      for post in post_divs:
        # Strip blockquotes so we don't duplicate quoted replies
        for quote in post.find_all(["div", "table"], class_="bbcode_quote"):
          quote.decompose()

        text = post.get_text(" ", strip=True)

        # Only keep substantial review paragraphs (>100 characters)
        if len(text) > 100:
          all_posts_data.append({
              "thread_title": item["title"],
              "post_content": text,
              "source_url": item["url"],
          })

    time.sleep(1.5)  # Courteous pause between threads
  except Exception as e:
    print(f"Error accessing thread {item['url']}: {e}")

if all_posts_data:
  df = pd.DataFrame(all_posts_data).drop_duplicates(subset=["post_content"])
  output_file = "teambhp_ev_detailed_reviews.csv"
  df.to_csv(output_file, index=False, encoding="utf-8")
  print(f"\nDONE: Successfully extracted {len(df)} user reviews/posts!")
  print(f"Saved to: {output_file}")
else:
  print("\nNo detailed posts were extracted.")