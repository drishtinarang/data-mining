import os
import re
import pandas as pd
import numpy as np

# 1. Locate the exact directory of this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def find_file(filename):
    # Check in script directory first
    p1 = os.path.join(SCRIPT_DIR, filename)
    if os.path.exists(p1):
        return p1
    # Check in current working directory
    p2 = os.path.join(os.getcwd(), filename)
    if os.path.exists(p2):
        return p2
    # Check in 'data cleaning' subfolder
    p3 = os.path.join(os.getcwd(), 'data cleaning', filename)
    if os.path.exists(p3):
        return p3
    return None

print("=" * 65)
print("     MEMBER 2: CHARGING INFRASTRUCTURE PREPROCESSING")
print("=" * 65)

# -------------------------------------------------------------
# 1. PARSE & CLEAN 'all_india_ev_stations_master.csv'
# -------------------------------------------------------------
file_master_path = find_file('all_india_ev_stations_master.csv')

if file_master_path:
    print(f"\n[1/2] Found master dataset at: {file_master_path}")
    df_raw = pd.read_csv(file_master_path, low_memory=False)
    print(f"      Total raw rows loaded: {len(df_raw)}")
    
    cleaned_master_records = []
    
    for _, row in df_raw.iterrows():
        raw_detail = str(row.get('Raw_Details', ''))
        search_city = str(row.get('Search_City', '')).strip()
        address = str(row.get('Address', '')).strip()
        
        parts = [p.strip() for p in raw_detail.split('|') if p.strip()]
        
        # 1. Extract Real Station Name
        station_name = parts[2] if len(parts) > 2 and parts[1] == '.' else 'EV Charging Station'
        
        # 2. Extract Full Address
        full_address = parts[3] if len(parts) > 3 else address
        combined_location_text = f"{full_address} {search_city}".lower()
        
        # 3. FIX "Unknown State": Extract actual Indian State from address/city
        state = 'Unknown'
        if any(w in combined_location_text for w in ['noida', 'greater noida', 'uttar pradesh', 'ghaziabad', 'lucknow']):
            state = 'Uttar Pradesh'
        elif any(w in combined_location_text for w in ['gurugram', 'gurgaon', 'faridabad', 'haryana', 'panchgaon', 'sohna']):
            state = 'Haryana'
        elif any(w in combined_location_text for w in ['delhi', 'connaught place', 'saket', 'hauz khas', 'aerocity']):
            state = 'Delhi'
        elif any(w in combined_location_text for w in ['bengaluru', 'bangalore', 'karnataka', 'whitefield', 'bellandur', 'electronic city']):
            state = 'Karnataka'
        elif any(w in combined_location_text for w in ['mumbai', 'pune', 'maharashtra', 'thane', 'navi mumbai']):
            state = 'Maharashtra'
        elif any(w in combined_location_text for w in ['chennai', 'tamil nadu', 'coimbatore']):
            state = 'Tamil Nadu'
        elif any(w in combined_location_text for w in ['hyderabad', 'telangana', 'secunderabad']):
            state = 'Telangana'
        elif any(w in combined_location_text for w in ['kolkata', 'west bengal']):
            state = 'West Bengal'
        elif 'delhi' in search_city.lower():
            state = 'Delhi'
        elif 'bengaluru' in search_city.lower():
            state = 'Karnataka'
            
        # 4. Extract Operator / Brand
        operator = 'Independent / Other'
        op_candidates = ['statiq', 'tata power', 'jio bp', 'jio-bp', 'chargezone', 
                         'shell recharge', 'eesl', 'zeon charging', 'sunfuel', 'ather']
        for cand in op_candidates:
            if cand in raw_detail.lower():
                operator = cand.title().replace('Jio Bp', 'Jio-bp Pulse')
                break
        if operator == 'Independent / Other' and len(parts) > 4:
            clean_part = parts[4].replace('(IN)', '').replace('(India)', '').strip()
            if not any(k in clean_part.lower() for k in ['fast dc', 'up to', 'connectors', 'points']):
                operator = clean_part
        
        # 5. Extract Charger Speed (Fast DC vs AC)
        speed = 'Fast DC' if 'fast dc' in raw_detail.lower() else 'Standard AC'
        
        # 6. Extract Power Rating in kW
        power_match = re.search(r'(\d+(?:\.\d+)?)\s*kW', raw_detail, re.IGNORECASE)
        power_kw = float(power_match.group(1)) if power_match else np.nan
        
        # 7. Extract Number of Points / Ports
        points_match = re.search(r'(\d+)\s*points', raw_detail, re.IGNORECASE)
        points = int(points_match.group(1)) if points_match else 1
        
        # 8. Extract Charging Cost (₹/kWh)
        cost_match = re.search(r'Cost:\s*\|\s*(\d+(?:\.\d+)?)', raw_detail, re.IGNORECASE)
        cost_per_kwh = float(cost_match.group(1)) if cost_match else np.nan
        
        cleaned_master_records.append({
            'station_name': station_name,
            'state': state,
            'search_city': search_city,
            'address': full_address,
            'operator': operator,
            'charging_speed': speed,
            'power_kw': power_kw,
            'charging_points': points,
            'cost_per_kwh': cost_per_kwh
        })

    df_cleaned_master = pd.DataFrame(cleaned_master_records)
    out_master = os.path.join(SCRIPT_DIR, 'cleaned_india_charging_stations_master.csv')
    df_cleaned_master.to_csv(out_master, index=False, encoding='utf-8')
    print(f"  -> SUCCESS! Saved {len(df_cleaned_master)} cleaned records to:")
    print(f"     '{out_master}'")
else:
    print("\n[!] WARNING: 'all_india_ev_stations_master.csv' NOT found.")

# -------------------------------------------------------------
# 2. CLEAN 'delhi_ev_charging_stations_osm.csv' (GEOSPATIAL GPS)
# -------------------------------------------------------------
file_delhi_path = find_file('delhi_ev_charging_stations_osm.csv')

if file_delhi_path:
    print(f"\n[2/2] Found Delhi OSM dataset at: {file_delhi_path}")
    df_delhi_raw = pd.read_csv(file_delhi_path, low_memory=False)
    raw_count = len(df_delhi_raw)
    
    cols_to_keep = ['osm_id', 'name', 'operator', 'brand', 'latitude', 'longitude', 'capacity']
    available_cols = [c for c in cols_to_keep if c in df_delhi_raw.columns]
    df_delhi = df_delhi_raw[available_cols].copy()
    
    # Filter valid coordinates
    df_delhi = df_delhi.dropna(subset=['latitude', 'longitude'])
    df_delhi = df_delhi[
        df_delhi['latitude'].between(28.3, 28)]