import os
import pandas as pd
import numpy as np

# 1. Locate directories (both script folder and parent data-mining folder)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)

def find_file(filename):
    for candidate in [
        os.path.join(SCRIPT_DIR, filename),
        os.path.join(PARENT_DIR, filename),
        os.path.join(os.getcwd(), filename),
        filename
    ]:
        if os.path.exists(candidate):
            return candidate
    return None

print("=" * 65)
print("        CLEANING DELHI EV CHARGING STATIONS DATASET")
print("=" * 65)

file_path = find_file('delhi_ev.csv')
if not file_path:
    print("ERROR: Could not find 'delhi_ev.csv'!")
    exit()

print(f"Found file at: {file_path}")
df_raw = pd.read_csv(file_path, low_memory=False)
print(f"Total raw records loaded: {len(df_raw)}")

# -------------------------------------------------------------
# 2. STANDARDIZE COORDINATES & GEOFENCE DELHI NCR
# -------------------------------------------------------------
df_raw.columns = [c.strip().lower() for c in df_raw.columns]

df_raw['latitude'] = pd.to_numeric(df_raw['latitude'], errors='coerce')
df_raw['longitude'] = pd.to_numeric(df_raw['longitude'], errors='coerce')

# Filter within Greater Delhi NCR bounds
df_clean = df_raw.dropna(subset=['latitude', 'longitude']).copy()
df_clean = df_clean[
    (df_clean['latitude'].between(28.3, 28.9)) & 
    (df_clean['longitude'].between(76.8, 77.5))
].reset_index(drop=True)

# Deduplicate co-located charging points (~11m)
df_clean['lat_r'] = df_clean['latitude'].round(4)
df_clean['lon_r'] = df_clean['longitude'].round(4)
df_clean = df_clean.drop_duplicates(subset=['lat_r', 'lon_r']).drop(columns=['lat_r', 'lon_r']).reset_index(drop=True)

print(f"Valid unique charging stations in Delhi NCR: {len(df_clean)}")

# -------------------------------------------------------------
# 3. LOCALITY & ZONE CLASSIFICATION IN DELHI NCR
# -------------------------------------------------------------
print("Classifying stations into Delhi sub-zones and districts...")

def get_delhi_zone_and_state(lat, lon):
    # Border areas
    if lon > 77.32 and lat < 28.65:
        return "Noida / Greater Noida", "Uttar Pradesh"
    elif lat < 28.48 and lon < 77.10:
        return "Gurugram", "Haryana"
    elif lat < 28.48 and lon >= 77.25:
        return "Faridabad", "Haryana"
    elif lon > 77.33 and lat >= 28.65:
        return "Ghaziabad", "Uttar Pradesh"
    
    # Internal Delhi Zones
    if 28.60 <= lat <= 28.66 and 77.18 <= lon <= 77.25:
        return "Central Delhi (Connaught Place / NDMC)", "Delhi"
    elif 28.50 <= lat < 28.60 and 77.18 <= lon <= 77.27:
        return "South Delhi (Hauz Khas / Saket / GK)", "Delhi"
    elif 28.52 <= lat <= 28.59 and 77.06 <= lon <= 77.15:
        return "South-West Delhi (Aerocity / Dwarka)", "Delhi"
    elif 28.60 <= lat <= 28.70 and 77.05 <= lon < 77.18:
        return "West Delhi (Janakpuri / Rajouri Garden)", "Delhi"
    elif lat > 28.66 and 77.12 <= lon <= 77.24:
        return "North Delhi (Civil Lines / Rohini / GTB)", "Delhi"
    elif 28.58 <= lat <= 28.68 and lon > 77.26:
        return "East Delhi (Mayur Vihar / Laxmi Nagar / IP)", "Delhi"
    else:
        return "Delhi Urban Outskirts", "Delhi"

localities = []
states = []
for _, row in df_clean.iterrows():
    loc, st = get_delhi_zone_and_state(row['latitude'], row['longitude'])
    localities.append(loc)
    states.append(st)

df_clean['region_zone'] = localities
df_clean['state'] = states

# -------------------------------------------------------------
# 4. STANDARDIZE OPERATORS
# -------------------------------------------------------------
print("Standardizing Delhi CPOs and network operators...")

def extract_delhi_operator(row):
    raw_text = " ".join([str(val) for val in row.values if pd.notna(val)]).lower()
    
    cpo_patterns = [
        ('eesl', 'EESL (Govt of India)'),
        ('energy efficie', 'EESL (Govt of India)'),
        ('electriva', 'ElectriVa'),
        ('terracharge', 'TerraCharge'),
        ('tata power', 'Tata Power'),
        ('ather', 'Ather Grid'),
        ('charj karo', 'Charge Karo'),
        ('charge karo', 'Charge Karo'),
        ('plug n go', 'Plug N Go'),
        ('statiq', 'Statiq'),
        ('jio bp', 'Jio-bp Pulse'),
        ('jio-bp', 'Jio-bp Pulse'),
        ('chargezone', 'ChargeZone'),
        ('blusmart', 'BluSmart Charge'),
        ('blu smart', 'BluSmart Charge'),
        ('yuma', 'Yuma Energy'),
        ('vida', 'Hero Vida'),
        ('honda', 'Honda E:Swap'),
        ('battery smart', 'Battery Smart'),
        ('sun mobility', 'Sun Mobility'),
        ('igl', 'IGL EV Charging'),
        ('okaya', 'Okaya')
    ]
    
    for pattern, clean_name in cpo_patterns:
        if pattern in raw_text:
            return clean_name
            
    if 'brand' in row and pd.notna(row['brand']) and str(row['brand']).strip() != '':
        return str(row['brand']).title()
        
    return 'Municipal / Public (Delhi Govt)'

df_clean['operator'] = df_clean.apply(extract_delhi_operator, axis=1)

# -------------------------------------------------------------
# 5. CHARGER SPEED & CAPACITY
# -------------------------------------------------------------
def get_speed(row):
    raw_text = " ".join([str(val) for val in row.values if pd.notna(val)]).lower()
    if any(k in raw_text for k in ['fast dc', 'ccs', 'combo', 'chademo', 'fast']):
        return 'Fast DC'
    return 'Standard AC'

df_clean['charging_speed'] = df_clean.apply(get_speed, axis=1)

if 'capacity' in df_clean.columns:
    df_clean['capacity_ports'] = pd.to_numeric(df_clean['capacity'], errors='coerce').fillna(1).astype(int)
else:
    df_clean['capacity_ports'] = 1

if 'name' in df_clean.columns:
    df_clean['station_name'] = df_clean['name'].fillna(df_clean['operator'] + ' Charging Station')
else:
    df_clean['station_name'] = df_clean['operator'] + ' Charging Station'

# -------------------------------------------------------------
# 6. EXPORT CLEANED FILE
# -------------------------------------------------------------
final_cols = [
    'station_name', 'state', 'region_zone', 'latitude', 'longitude', 
    'operator', 'charging_speed', 'capacity_ports'
]
df_final = df_clean[final_cols].copy()

output_file = os.path.join(SCRIPT_DIR, 'cleaned_delhi_ev_stations.csv')
df_final.to_csv(output_file, index=False, encoding='utf-8')

print("\n" + "=" * 65)
print(f"SUCCESS! Cleaned dataset saved to: '{os.path.basename(output_file)}'")
print("=" * 65)

print("\n--- DISTRIBUTION BY DELHI NCR ZONES ---")
print(df_final['region_zone'].value_counts().to_string())

print("\n--- TOP CHARGING OPERATORS IN DELHI ---")
print(df_final['operator'].value_counts().head(8).to_string())

print("\n--- CHARGING SPEED BREAKDOWN ---")
print(df_final['charging_speed'].value_counts().to_string())

print("\n--- SAMPLE RECORDS ---")
print(df_final[['region_zone', 'operator', 'charging_speed', 'capacity_ports']].head(5).to_string())