"""
India EV Vehicles — Basic Info Extractor
Gets: Brand, Model, Range (km), Battery (kWh), Price (Rs), Type
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

# -------------------------------------------------------
# SOURCE 1: ev-database.org — Technical specs
# -------------------------------------------------------
def get_ev_database():
    print("Fetching from ev-database.org ...")
    url  = "https://ev-database.org/"
    resp = requests.get(url, headers=HEADERS, timeout=30)
    soup = BeautifulSoup(resp.text, "html.parser")

    records = []
    for card in soup.select(".list-item"):
        try:
            name    = card.select_one(".list-item-title h2").text.strip()
            specs   = {s["title"]: s.text.strip() for s in card.select(".list-item-specs span") if s.has_attr("title")}

            records.append({
                "model"             : name,
                "range_km"          : specs.get("Rated Range", "N/A"),
                "battery_kwh"       : specs.get("Battery Capacity", "N/A"),
                "fast_charge_kw"    : specs.get("Fastcharge Power", "N/A"),
                "efficiency_wh_km"  : specs.get("Energy Consumption", "N/A"),
            })
        except:
            continue

    return pd.DataFrame(records)


# -------------------------------------------------------
# SOURCE 2: CarWale — India prices & availability
# -------------------------------------------------------
def get_carwale_ev():
    print("Fetching from CarWale India ...")
    url  = "https://www.carwale.com/electric-cars/"
    resp = requests.get(url, headers=HEADERS, timeout=30)
    soup = BeautifulSoup(resp.text, "html.parser")

    records = []
    # CarWale car cards
    for card in soup.select('[data-tracking-id="car-card"]'):
        try:
            model  = card.select_one("h3, h2, .o-eEOWUf").text.strip()
            price  = card.select_one(".o-ckVAcC, .price").text.strip()
            records.append({"model": model, "price_india": price})
        except:
            continue

    # fallback selector
    if not records:
        for card in soup.select("article, .carCard, .car-card"):
            try:
                model = card.select_one("h2, h3").text.strip()
                price = card.select_one('[class*="price"], [class*="Price"]').text.strip()
                records.append({"model": model, "price_india": price})
            except:
                continue

    return pd.DataFrame(records)


# -------------------------------------------------------
# SOURCE 3: Hardcoded popular India EVs (always works!)
# -------------------------------------------------------
def get_known_india_evs():
    """
    Curated list of EVs currently available/launched in India (2024-25)
    """
    evs = [
        # Brand,              Model,                  Type,    Range_km, Battery_kWh, Price_Rs_Lakh
        ("Tata",              "Nexon EV",              "SUV",   465,      40.5,        "14.74 - 19.94"),
        ("Tata",              "Punch EV",              "SUV",   421,      35.0,        "10.99 - 15.49"),
        ("Tata",              "Tiago EV",              "Hatch", 315,      24.0,        "8.49 - 11.89"),
        ("Tata",              "Curvv EV",              "SUV",   502,      55.0,        "17.49 - 21.99"),
        ("Tata",              "Tigor EV",              "Sedan", 306,      26.0,        "12.49 - 13.75"),
        ("MG",                "Windsor EV",            "SUV",   331,      38.0,        "13.50 - 15.50"),
        ("MG",                "ZS EV",                 "SUV",   461,      50.3,        "18.98 - 23.98"),
        ("MG",                "Comet EV",              "Micro", 230,      17.3,        "6.99 - 9.99"),
        ("Mahindra",          "XEV 9e",                "SUV",   656,      79.0,        "21.90 - 30.50"),
        ("Mahindra",          "XEV 7e",                "SUV",   542,      79.0,        "18.90 - 28.90"),
        ("Mahindra",          "BE 6",                  "SUV",   682,      79.0,        "18.90 - 26.90"),
        ("Hyundai",           "Creta Electric",        "SUV",   473,      51.4,        "17.99 - 23.49"),
        ("Hyundai",           "Ioniq 5",               "SUV",   631,      72.6,        "44.95 - 46.95"),
        ("Hyundai",           "Ioniq 6",               "Sedan", 614,      77.4,        "53.90"),
        ("Kia",               "EV6",                   "SUV",   528,      77.4,        "60.97 - 65.97"),
        ("Kia",               "EV9",                   "SUV",   541,      99.8,        "1.35 Cr"),
        ("BMW",               "i4",                    "Sedan", 590,      83.9,        "72.50 - 78.90"),
        ("BMW",               "iX",                    "SUV",   630,      111.5,       "1.18 - 1.33 Cr"),
        ("BMW",               "i7",                    "Sedan", 625,      101.7,       "1.95 Cr"),
        ("Mercedes",          "EQS",                   "Sedan", 770,      107.8,       "1.55 - 2.05 Cr"),
        ("Mercedes",          "EQB",                   "SUV",   423,      66.5,        "74.50"),
        ("Mercedes",          "EQE",                   "SUV",   617,      90.6,        "1.05 - 1.35 Cr"),
        ("Audi",              "e-tron GT",             "Sedan", 500,      93.4,        "1.80 - 2.05 Cr"),
        ("Audi",              "Q8 e-tron",             "SUV",   582,      114.0,       "1.14 - 1.19 Cr"),
        ("Volvo",             "EX40",                  "SUV",   530,      82.0,        "55.90"),
        ("Volvo",             "EX90",                  "SUV",   600,      107.0,       "1.28 Cr"),
        ("BYD",               "Atto 3",                "SUV",   521,      60.5,        "33.90 - 34.90"),
        ("BYD",               "Seal",                  "Sedan", 650,      82.5,        "41.00 - 53.00"),
        ("BYD",               "e6",                    "MPV",   520,      71.7,        "29.15"),
        ("Toyota",            "bZ4X",                  "SUV",   516,      71.4,        "49.90 - 51.90"),
        ("Lexus",             "UX 300e",               "SUV",   400,      72.8,        "74.90"),
        ("Porsche",           "Taycan",                "Sedan", 484,      93.4,        "1.87 - 3.10 Cr"),
        ("Ola Electric",      "S1 Pro (2-Wheeler)",    "Bike",  195,      4.0,         "1.30 - 1.50"),
        ("Ather",             "450X (2-Wheeler)",      "Bike",  146,      3.7,         "1.40 - 1.55"),
        ("TVS",               "iQube (2-Wheeler)",     "Bike",  145,      5.1,         "1.05 - 1.30"),
        ("Bajaj",             "Chetak (2-Wheeler)",    "Bike",  126,      3.0,         "1.15 - 1.35"),
        ("Hero Electric",     "Optima (2-Wheeler)",    "Bike",  82,       1.3,         "0.68 - 0.74"),
        ("Greaves",           "Ampere Magnus (2W)",    "Bike",  121,      1.8,         "0.79 - 0.99"),
    ]

    df = pd.DataFrame(evs, columns=[
        "brand", "model", "vehicle_type",
        "range_km", "battery_kwh", "price_rs_lakh"
    ])
    return df


# -------------------------------------------------------
# MAIN — Run all sources
# -------------------------------------------------------
print("=" * 60)
print("  INDIA EV VEHICLES — DATA EXTRACTION")
print("=" * 60)

# Get curated India EV list (always works)
df_india = get_known_india_evs()

# Try live scraping too
try:
    df_web = get_ev_database()
    print(f"  ev-database.org : {len(df_web)} vehicles fetched")
except Exception as e:
    print(f"  ev-database.org : Failed ({e})")
    df_web = pd.DataFrame()

try:
    df_cw = get_carwale_ev()
    print(f"  CarWale         : {len(df_cw)} vehicles fetched")
except Exception as e:
    print(f"  CarWale         : Failed ({e})")
    df_cw = pd.DataFrame()

# Save all outputs
df_india.to_csv("india_ev_vehicles.csv", index=False, encoding="utf-8")
if not df_web.empty:
    df_web.to_csv("ev_database_specs.csv", index=False, encoding="utf-8")
if not df_cw.empty:
    df_cw.to_csv("carwale_ev_india.csv", index=False, encoding="utf-8")

# Print summary
print("\n" + "=" * 60)
print(f"  Total known India EVs : {len(df_india)}")
print("=" * 60)
print("\nFULL LIST:")
print(df_india.to_string(index=False))

print("\nBY BRAND:")
print(df_india['brand'].value_counts().to_string())

print("\nBY VEHICLE TYPE:")
print(df_india['vehicle_type'].value_counts().to_string())

print(f"\nFiles saved:")
print(f"  india_ev_vehicles.csv   <- Main curated list")
print(f"  ev_database_specs.csv   <- Technical specs (if scraped)")
print(f"  carwale_ev_india.csv    <- India prices (if scraped)")