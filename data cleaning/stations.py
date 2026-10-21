import os
import requests
import numpy as np
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)

# ==============================================================================
# 🔑 PASTE YOUR OPEN CHARGE MAP API KEY HERE:
# ==============================================================================
API_KEY = "a4011276-2d5b-4323-8fc0-47472bec8975"
# ==============================================================================

print("=" * 70)
print("   PAN-INDIA EV CHARGING STATIONS EXTRACTION (ALL 28 STATES)")
print("=" * 70)

# -------------------------------------------------------------
# 1. FETCH FULL DATASET FROM OPEN CHARGE MAP API
# -------------------------------------------------------------
url = "https://api.openchargemap.io/v3/poi"

params = {
    "countrycode": "IN",          # ISO-2 country code for India
    "maxresults": 5000,           # Fetch up to 5,000 stations
    "compact": "false",           # Full metadata
    "verbose": "false",
    "key": API_KEY
}

headers = {
    "User-Agent": "PanIndiaEVDataMining/1.0"
}

print(f"Connecting to Open Charge Map API for Country: INDIA (IN)...")

try:
    response = requests.get(url, params=params, headers=headers, timeout=90)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ SUCCESS! Retrieved {len(data)} stations from Open Charge Map API.")
    else:
        print(f"❌ API Error {response.status_code}: {response.text}")
        exit()
except Exception as e:
    print(f"❌ Connection error: {e}")
    exit()

# -------------------------------------------------------------
# 2. INDIAN REFERENCE GRID FOR ACCURATE STATE & CITY RESOLUTION
# -------------------------------------------------------------
# Used to fill in missing/abbreviated states in OCM records
INDIAN_CITIES = [
    ("Bengaluru", "Karnataka", 12.9716, 77.5946),
    ("Mysuru", "Karnataka", 12.2958, 76.6394),
    ("Mangaluru", "Karnataka", 12.9141, 74.8560),
    ("Hubballi", "Karnataka", 15.3647, 75.1240),
    ("Mumbai", "Maharashtra", 19.0760, 72.8777),
    ("Pune", "Maharashtra", 18.5204, 73.8567),
    ("Thane / Navi Mumbai", "Maharashtra", 19.2183, 72.9781),
    ("Nagpur", "Maharashtra", 21.1458, 79.0882),
    ("Nashik", "Maharashtra", 19.9975, 73.7898),
    ("Delhi", "Delhi", 28.6139, 77.2090),
    ("Gurugram", "Haryana", 28.4595, 77.0266),
    ("Faridabad", "Haryana", 28.4089, 77.3178),
    ("Noida / Greater Noida", "Uttar Pradesh", 28.5355, 77.3910),
    ("Ghaziabad", "Uttar Pradesh", 28.6692, 77.4538),
    ("Lucknow", "Uttar Pradesh", 26.8467, 80.9462),
    ("Kanpur", "Uttar Pradesh", 26.4499, 80.3319),
    ("Agra", "Uttar Pradesh", 27.1767, 78.0081),
    ("Varanasi", "Uttar Pradesh", 25.3176, 82.9739),
    ("Kochi / Ernakulam", "Kerala", 9.9312, 76.2673),
    ("Thiruvananthapuram", "Kerala", 8.5241, 76.9366),
    ("Kozhikode", "Kerala", 11.2588, 75.7804),
    ("Chennai", "Tamil Nadu", 13.0827, 80.2707),
    ("Coimbatore", "Tamil Nadu", 11.0168, 76.9558),
    ("Madurai", "Tamil Nadu", 9.9252, 78.1198),
    ("Hyderabad", "Telangana", 17.3850, 78.4867),
    ("Ahmedabad", "Gujarat", 23.0225, 72.5714),
    ("Surat", "Gujarat", 21.1702, 72.8311),
    ("Vadodara", "Gujarat", 22.3072, 73.1812),
    ("Jaipur", "Rajasthan", 26.9124, 75.7873),
    ("Udaipur", "Rajasthan", 24.5854, 73.7125),
    ("Kolkata", "West Bengal", 22.5726, 88.3639),
    ("Chandigarh", "Chandigarh", 30.7333, 76.7794),
    ("Ludhiana", "Punjab", 30.9010, 75.8573),
    ("Amritsar", "Punjab", 31.6340, 74.8723),
    ("Bhopal", "Madhya Pradesh", 23.2599, 77.4126),
    ("Indore", "Madhya Pradesh", 22.7196, 75.8577),
    ("Patna", "Bihar", 25.5941, 85.1376),
    ("Bhubaneswar", "Odisha", 20.2961, 85.8245),
    ("Visakhapatnam", "Andhra Pradesh", 17.6868, 83.2185),
    ("Vijayawada", "Andhra Pradesh", 16.5062, 80.6480),
    ("Raipur", "Chhattisgarh", 21.2514, 81.6296),
    ("Ranchi", "Jharkhand", 23.3441, 85.3096),
    ("Dehradun", "Uttarakhand", 30.3165, 78.0322),
    ("Shimla", "Himachal Pradesh", 31.1048, 77.1734),
    ("Panaji", "Goa", 15.4909, 73.8278),
    ("Srinagar", "Jammu and Kashmir", 34.0837, 74.7973),
    ("Puducherry", "Puducherry", 11.9416, 79.8083),
    ("Guwahati", "Assam", 26.1445, 91.7362)
]

city_coords = np.array([[c[2], c[3]] for c in INDIAN_CITIES])

def get_nearest_state_and_city(lat, lon):
    dists = np.sqrt((city_coords[:, 0] - lat)**2 + (city_coords[:, 1] - lon)**2)
    idx = np.argmin(dists)
    return INDIAN_CITIES[idx][0], INDIAN_CITIES[idx][1]

# -------------------------------------------------------------
# 3. PARSE EVERY STATION RECORD & EXTRACT TECHNICAL SPECS
# -------------------------------------------------------------
print("Parsing stations, coordinates, operators, and AC/DC speeds...")
parsed_records = []

for item in data:
    addr = item.get('AddressInfo', {})
    operator_info = item.get('OperatorInfo', {})
    connections = item.get('Connections', [])
    status_info = item.get('StatusType', {})
    
    # Coordinates
    lat = addr.get('Latitude')
    lon = addr.get('Longitude')
    if lat is None or lon is None:
        continue
        
    lat = float(lat)
    lon = float(lon)
    
    # Filter to Indian geographical bounds (Lat 6.5-37.5, Lon 68-97.5)
    if not (6.5 <= lat <= 37.5 and 68.0 <= lon <= 97.5):
        continue

    # Station Identity
    station_id = item.get('ID')
    station_name = addr.get('Title', 'Public EV Charging Station').strip()
    raw_address = addr.get('AddressLine1', '').strip()
    pincode = addr.get('Postcode', '').strip()
    
    # State & City: Use Address info if present, otherwise geospatial engine
    raw_state = addr.get('StateOrProvince', '')
    raw_city = addr.get('Town', '')
    
    nearest_city, nearest_state = get_nearest_state_and_city(lat, lon)
    
    final_state = raw_state.strip().title() if raw_state and len(raw_state.strip()) > 3 else nearest_state
    final_city = raw_city.strip().title() if raw_city and len(raw_city.strip()) > 2 else nearest_city

    # Operator / CPO
    operator = operator_info.get('Title', '').strip() if operator_info else ''
    if not operator or operator.lower() in ['unknown', '(unknown operator)', 'none', '']:
        operator = 'Independent / Municipal'

    # Connector Types & Power (kW)
    connector_names = []
    power_kw_list = []
    total_ports = 0
    is_fast_dc = False
    
    for conn in connections:
        conn_title = conn.get('ConnectionType', {}).get('Title')
        if conn_title:
            connector_names.append(conn_title)
            
        qty = conn.get('Quantity')
        total_ports += int(qty) if qty and str(qty).isdigit() else 1
        
        power = conn.get('PowerKW')
        if power:
            try:
                p_val = float(power)
                power_kw_list.append(p_val)
                if p_val >= 22.0:
                    is_fast_dc = True
            except:
                pass
                
        level_title = conn.get('Level', {}).get('Title', '').lower()
        if any(k in level_title for k in ['fast', 'dc', 'level 3']):
            is_fast_dc = True

    # Speed Classification
    speed = 'Fast DC' if is_fast_dc else 'Standard AC'
    max_power = max(power_kw_list) if power_kw_list else (50.0 if speed == 'Fast DC' else 7.4)
    connectors_str = ", ".join(sorted(set(connector_names))) if connector_names else ('CCS (Type 2)' if speed == 'Fast DC' else 'Type 2 AC')
    total_ports = max(total_ports, 1)

    # Cost / Fee info
    usage_cost = item.get('UsageCost') or 'Unknown'
    
    # Status
    is_operational = status_info.get('IsOperational', True) if status_info else True

    parsed_records.append({
        'station_id': station_id,
        'station_name': station_name,
        'state': final_state,
        'city': final_city,
        'address': raw_address,
        'pincode': pincode,
        'latitude': lat,
        'longitude': lon,
        'operator': operator,
        'charging_speed': speed,
        'max_power_kw': max_power,
        'total_ports': total_ports,
        'connector_types': connectors_str,
        'usage_cost': usage_cost,
        'is_operational': is_operational
    })

df = pd.DataFrame(parsed_records)

# Deduplicate co-located points
df = df.drop_duplicates(subset=['station_id']).reset_index(drop=True)

# Standardize Common State Names
state_mapping = {
    'Nct Of Delhi': 'Delhi', 'New Delhi': 'Delhi',
    'Bangalore': 'Karnataka', 'Bengaluru': 'Karnataka',
    'State Of Karnataka': 'Karnataka', 'State Of Maharashtra': 'Maharashtra',
    'State Of Tamil Nadu': 'Tamil Nadu', 'State Of Gujarat': 'Gujarat'
}
df['state'] = df['state'].replace(state_mapping)

# Save Final Clean File
output_file = os.path.join(SCRIPT_DIR, 'pan_india_ev_charging_stations_complete.csv')
df.to_csv(output_file, index=False, encoding='utf-8')

print("\n" + "=" * 70)
print(f"🎉 SUCCESS! Extracted {len(df)} stations across India!")
print(f"📁 Saved to: '{os.path.basename(output_file)}'")
print("=" * 70)

print("\n📍 STATIONS PER STATE (Top 15):")
print(df['state'].value_counts().head(15).to_string())

print("\n⚡ TOP CHARGING NETWORK OPERATORS (CPOs):")
print(df['operator'].value_counts().head(10).to_string())

print("\n🔌 CHARGER SPEED (FAST DC VS STANDARD AC):")
print(df['charging_speed'].value_counts().to_string())

print("\n🔍 SAMPLE ROWS PREVIEW:")
print(df[['station_name', 'state', 'city', 'operator', 'charging_speed', 'max_power_kw']].head(5).to_string())