import time
from bs4 import BeautifulSoup 
import requests
import pandas as pd

print(">>> Scraping Consumer Complaints for Indian EVs...")

# Target complaint hubs for leading Indian EV manufacturers
search_targets = [
    "tata-motors",
    "ola-electric",
    "ather-energy",
]

complaints = []

for company in search_targets:
  url = f"https://www.consumercomplaints.in/?search={company}+battery+charging"
  print(f"Mining complaints for {company}...")

  try:
    res = requests.get(url, impersonate="chrome120", timeout=20)
    if res.status_code == 200:
      soup = BeautifulSoup(res.text, "html.parser")

      # Consumercomplaints structures entries inside complaint blocks
      cards = soup.find_all("div", class_=lambda x: x and "complaint-row" in x.lower()) or soup.find_all("tr")

      for card in cards:
        link_tag = card.find("a", href=lambda h: h and "/complaint/" in h)
        if not link_tag:
          continue

        title = link_tag.get_text(strip=True)
        # Check snippet or body inside card
        body_tag = card.find(["td", "div", "p"], class_=lambda c: c and ("text" in c or "body" in c))
        body = body_tag.get_text(strip=True) if body_tag else title

        if len(title) > 10:
          complaints.append({
              "entity": company,
              "complaint_title": title,
              "complaint_summary": body,
              "source": "ConsumerComplaints.in",
          })
    else:
      print(f"  -> Failed with status {res.status_code}")

    time.sleep(2)

  except Exception as e:
    print(f"  -> Error: {e}")

df = pd.DataFrame(complaints).drop_duplicates(subset=["complaint_title"])
df.to_csv("ev_consumer_complaints.csv", index=False, encoding="utf-8")
print(f"SUCCESS: Saved {len(df)} complaints to 'ev_consumer_complaints.csv'")