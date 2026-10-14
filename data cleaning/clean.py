import os
import re
import pandas as pd
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

print("=" * 60)
print("STARTING HIGH-YIELD DATA CLEANING PIPELINE (COMPREHENSIVE EV FILTER)")
print("=" * 60)

# 1. Download required NLTK resources
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)
nltk.download('omw-1.4', quiet=True)

stop_words = set(stopwords.words('english'))
forum_noise_words = {
    'teambhp', 'quote', 'originally', 'posted', 
    'mod', 'note', 'mods', 'thread', 'reportcopy', 'resolved'
}
all_stopwords = stop_words.union(forum_noise_words)
lemmatizer = WordNetLemmatizer()

# Comprehensive EV regex covering cars, trucks, 2W, 3W, commercial EVs, specs, and brands
EV_KEYWORDS_PATTERN = re.compile(
    r'\b('
    # Core EV terminology
    r'ev|evs|electric|battery|charging|charger|charge|range|kms|km|soc|regen|fastcharge|dc|ac|wallbox|'
    r'kwh|motive|kilowatt|pmsm|bms|plug|inverter|motor|drivetrain|zero emission|'
    # Vehicles (Cars, Trucks, Buses, Scooters, Vans)
    r'car|cars|truck|trucks|scooter|scooters|bike|bikes|bus|buses|cab|cabs|auto|rickshaw|van|lorry|'
    r'commercial|fleet|hauler|pickup|suv|sedan|hatchback|'
    # Brands & Models (Indian & Global EV Ecosystem)
    r'ola|ather|nexon|tiago|tigor|punch|harrier|safari|curvv|windsor|comet|zsev|mg|'
    r'chetak|iqube|tvs|bajaj|hero|vida|matter|revolt|ultraviolette|ola electric|'
    r'mahindra|xuv400|be05|born electric|supro|e2o|treo|'
    r'byd|atto|seal|e6|hyundai|kona|ioniq|kia|ev6|ev9|'
    r'tesla|cybertruck|rivian|lucid|polestar|volvo|ex30|xc40|'
    r'eicher|ashok|leyland|switch|tata motors|tata ace|ace ev'
    r')\b', re.IGNORECASE
)

def clean_forum_text(raw_text):
    if not isinstance(raw_text, str) or not raw_text.strip():
        return ""
    
    text = raw_text
    # Remove web URLs
    text = re.sub(r'https?://\S+|www\.\S+', ' ', text)
    # Remove forum quoting noise & @mentions
    text = re.sub(r'Quote:\s*Originally Posted by\s*[\w\d_]+', ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'Mod\s*Note:?', ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'@[\w\d_]+', ' ', text)
    # Remove scraping debris
    text = re.sub(r'ReportCopy\w*', ' ', text, flags=re.IGNORECASE)
    # Keep only alphabetic characters
    text = re.sub(r'[^a-zA-Z\s]', ' ', text)
    # Lowercase and split
    words = text.lower().split()
    # Filter stopwords and lemmatize
    cleaned_tokens = [
        lemmatizer.lemmatize(w)
        for w in words
        if w not in all_stopwords and len(w) >= 2
    ]
    return " ".join(cleaned_tokens)

def get_column_value(row, candidate_cols):
    for col in candidate_cols:
        if col in row.index and pd.notna(row[col]):
            val = str(row[col]).strip()
            if val and val.lower() != 'nan':
                return val
    return ''

# 2. Collect records from files
records = []

# File 1: TeamBHP Detailed Reviews
if os.path.exists('teambhp_ev_detailed_reviews.csv'):
    print("[1/8] Reading teambhp_ev_detailed_reviews.csv...")
    df1 = pd.read_csv('teambhp_ev_detailed_reviews.csv', low_memory=False)
    for _, row in df1.iterrows():
        title = get_column_value(row, ['thread_title', 'title'])
        content = get_column_value(row, ['post_content', 'content', 'review'])
        text = (title + ". " + content).strip()
        if len(text) > 5:
            records.append({'source': 'TeamBHP', 'raw_text': text})

# File 2: TeamBHP Threads
if os.path.exists('teambhp_ev_threads.csv'):
    print("[2/8] Reading teambhp_ev_threads.csv...")
    df2 = pd.read_csv('teambhp_ev_threads.csv', low_memory=False)
    for _, row in df2.iterrows():
        title = get_column_value(row, ['thread_title', 'title'])
        content = get_column_value(row, ['post_content', 'content', 'snippet', 'description'])
        text = (title + ". " + content).strip()
        if len(text) > 5:
            records.append({'source': 'TeamBHP Threads', 'raw_text': text})

# File 3: Consumer Complaints
if os.path.exists('ev_consumer_complaints.csv'):
    print("[3/8] Reading ev_consumer_complaints.csv...")
    df3 = pd.read_csv('ev_consumer_complaints.csv', low_memory=False)
    for _, row in df3.iterrows():
        title = get_column_value(row, ['complaint_title', 'title'])
        summary = get_column_value(row, ['complaint_summary', 'summary', 'description'])
        text = (title + ". " + summary).strip()
        if len(text) > 5:
            records.append({'source': 'Consumer Complaints', 'raw_text': text})

# File 4: Indian EV Reviews
if os.path.exists('indian_ev_reviews_dataset.csv'):
    print("[4/8] Reading indian_ev_reviews_dataset.csv...")
    df4 = pd.read_csv('indian_ev_reviews_dataset.csv', low_memory=False)
    for _, row in df4.iterrows():
        title = get_column_value(row, ['title'])
        review = get_column_value(row, ['review_text', 'review', 'text'])
        text = (title + ". " + review).strip()
        if len(text) > 5:
            records.append({'source': 'EV Reviews', 'raw_text': text})

# File 5: CarWale Live Reviews
if os.path.exists('carwale_live_reviews.csv'):
    print("[5/8] Reading carwale_live_reviews.csv...")
    df5 = pd.read_csv('carwale_live_reviews.csv', low_memory=False)
    for _, row in df5.iterrows():
        title = get_column_value(row, ['title', 'review_title', 'heading'])
        review = get_column_value(row, ['review_text', 'review', 'comment', 'description'])
        text = (title + ". " + review).strip()
        if len(text) > 5:
            records.append({'source': 'CarWale', 'raw_text': text})

# File 6: Reddit EV Reviews
if os.path.exists('reddit_ev_reviews.csv'):
    print("[6/8] Reading reddit_ev_reviews.csv...")
    df6 = pd.read_csv('reddit_ev_reviews.csv', low_memory=False)
    for _, row in df6.iterrows():
        title = get_column_value(row, ['title', 'post_title'])
        comment = get_column_value(row, ['comment', 'selftext', 'body', 'review_text', 'post_content'])
        text = (title + ". " + comment).strip()
        if len(text) > 5:
            records.append({'source': 'Reddit', 'raw_text': text})

# File 7: Master EV Reviews 600+
if os.path.exists('master_ev_reviews_600plus.csv'):
    print("[7/8] Reading master_ev_reviews_600plus.csv...")
    df7 = pd.read_csv('master_ev_reviews_600plus.csv', low_memory=False)
    for _, row in df7.iterrows():
        title = get_column_value(row, ['title', 'review_title'])
        review = get_column_value(row, ['review_text', 'review', 'text', 'content', 'description'])
        text = (title + ". " + review).strip()
        if len(text) > 5:
            records.append({'source': 'Master EV Reviews', 'raw_text': text})

master_df = pd.DataFrame(records)
print(f"Total raw records collected across all sources: {len(master_df)}")

# 3. Clean text
print("Cleaning text and lemmatizing words...")
master_df['cleaned_text'] = master_df['raw_text'].apply(clean_forum_text)

# 4. Deduplicate based on cleaned text
master_df = master_df.drop_duplicates(subset=['cleaned_text']).reset_index(drop=True)

# 5. Keep non-empty cleaned strings (at least 2 words)
master_df = master_df[master_df['cleaned_text'].str.split().str.len() >= 2].reset_index(drop=True)
print(f"Final clean records retained: {len(master_df)}")

# 6. Export to CSV
output_csv = 'cleaned_ev_reviews_corpus.csv'
master_df.to_csv(output_csv, index=False, encoding='utf-8')
print("Successfully written to:", output_csv)

# 7. Print summary statistics
print("\n" + "=" * 60)
print("SUMMARY BY SOURCE:")
print("=" * 60)
print(master_df['source'].value_counts())
print("=" * 60)