import os
import time
import requests
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)

print("=" * 65)
print("FETCHING EV CHARGING STATIONS ACROSS INDIA (REGIONAL CLUSTERS)")
print("=" * 65)

# Bounding boxes for India's major EV corridors
clusters = [
    {"region": "Delhi NCR (Delhi, Gurugram, Noida, Faridabad)", "bbox": "28.1,76.6,28.9,77.7"},
    {"region": "Karnataka (Bengaluru & Mysuru)", "bbox": "12.0,76.4,13.5,78.0"},
    {"region": "Maharashtra (Mumbai, Pune, Thane)", "bbox": "18.3,72.6,19.5,74.2"},
    {"region": "Tamil Nadu (Chennai & Coimbatore)", "bbox": "10.8,76.8,13.4,80.4"},
    {"region": "Telangana (Hyderabad)", "bbox": "17.1,78.1,17.7,78.8"},
    {"region": "Gujarat (Ahmedabad, Surat, Vadodara)", "bbox": "21.0,72.5,23.3,73.4"},
    {"region": "Kerala (Kochi & Trivandrum)", "bbox": "8.4,76.1,10.2,77.1"},
    {"region": "West Bengal (Kolkata)", "bbox": "22.3,88.1,22.9,88.6"},
    {"region": "Rajasthan (Jaipur & NH-48 Corridor)", "bbox": "26.6,75.5,27.9,76.8"},
    {"region": "Chandigarh & Punjab Corridor", "bbox": "30.5,76.4,31.0,77.0"}
]

overpass_url = "https://overpass-api.de/api/interpreter"
headers = {'User-Agent': 'AcademicDataMiningEVStudy/1.0'}

all_records = []

for i, cl in enumerate(clusters, 1):
    print(f"[{i}/{len(clusters)}] Fetching {cl['region']} ...", end=" ", flush=True)
    
    query = f"""
    [out:json][timeout:30];
    (
      node["amenity"="charging_station"]({cl['bbox']});
      way["amenity"="charging_station"]({cl['bbox']});
    );
    out center tags;
    """
    
    try:
        response = requests.post(overpass_url, data={'data': query}, headers=headers, timeout=35)
        if response.status_code == 200:
            elements = response.json().get('elements', [])
            print(f"Found {len(elements)} stations!")
            
            for el in elements:
                tags = el.get('tags', {})
                lat = el.get('lat') if 'lat' in el else el.get('center', {}).get('lat')
                lon = el.get('lon') if 'lon' in el else el.get('center', {}).get('lon')
                
                socket = (tags.get('socket:type2_combo') or 
                          tags.get('socket:type2') or 
                          tags.get('socket:chademo') or 
                          tags.get('socket') or 
                          'Standard')
                
                is_fast = 'Fast DC' if any(k in str(tags).lower() for k in ['fast', 'combo', 'ccs', 'chademo', 'dc']) else 'Standard AC'
                
                all_records.append({
                    'osm_id': el.get('id'),
                    'region': cl['region'].split('(')[0].strip(),
                    'station_name': tags.get('name', 'Public EV Station'),
                    'operator': tags.get('operator') or tags.get('brand') or 'Independent / Public',
                    'latitude': lat,
                    'longitude': lon,
                    'charging_speed': is_fast,
                    'connector_type': socket,
                    'capacity_ports': tags.get('capacity', '1'),
                    'opening_hours': tags.get('opening_hours', 'Unknown'),
                    'fee': tags.get('fee', 'Unknown')
                })
        else:
            print(f"HTTP {response.status_code}")
    except Exception as e:
        print(f"Skipped (timeout)")
        
    time.sleep(1)  # Polite delay between requests

df = pd.DataFrame(all_records)

# Deduplicate co-located points
df = df.drop_duplicates(subset=['osm_id']).dropna(subset=['latitude', 'longitude']).reset_index(drop=True)

output_file = os.path.join(SCRIPT_DIR, 'all_india_osm_charging_stations_complete.csv')
df.to_csv(output_file, index=False, encoding='utf-8')

print("\n" + "=" * 65)
print(f"SUCCESS! Total nationwide stations extracted: {len(df)}")
print(f"Saved to: '{output_file}'")
print("=" * 65)
print("\nRegional breakdown:")
print(df['region'].value_counts())
print("\nTop Operators:")
print(df['operator'].value_counts().head(8))