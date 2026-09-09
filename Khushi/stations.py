import requests
import pandas as pd
import time

# -------------------------------------------------------
# 1. Area to search
# -------------------------------------------------------
CITY = "Delhi"

# -------------------------------------------------------
# 2. Overpass API
# -------------------------------------------------------
overpass_url = "https://overpass-api.de/api/interpreter"

query = f"""
[out:json][timeout:60];

area["name"="{CITY}"]["boundary"="administrative"]->.searchArea;

(
    node["amenity"="charging_station"](area.searchArea);
    way["amenity"="charging_station"](area.searchArea);
    relation["amenity"="charging_station"](area.searchArea);
);

out center tags;
"""

# -------------------------------------------------------
# 3. Send request
# -------------------------------------------------------
print("Downloading charging station data from OpenStreetMap...")
print("Please wait...")

headers = {
    "User-Agent": "EVChargingDataMiningProject/1.0 (student project)",
    "Accept": "application/json",
    "Content-Type": "application/x-www-form-urlencoded"
}

# If you just received a 406, wait before retrying
time.sleep(30)

response = requests.post(
    overpass_url,
    data={"data": query},
    headers=headers,
    timeout=120
)

print("HTTP Status:", response.status_code)

response.raise_for_status()

data = response.json()

print(f"Total OSM objects found: {len(data['elements'])}")

# -------------------------------------------------------
# 4. Extract useful information
# -------------------------------------------------------
stations = []

for element in data["elements"]:

    tags = element.get("tags", {})

    # Node has direct latitude/longitude
    if element["type"] == "node":
        latitude = element.get("lat")
        longitude = element.get("lon")

    # Ways/relations have center coordinates
    else:
        center = element.get("center", {})
        latitude = center.get("lat")
        longitude = center.get("lon")

    stations.append({
        "osm_id": element.get("id"),
        "osm_type": element.get("type"),
        "name": tags.get("name"),
        "operator": tags.get("operator"),
        "brand": tags.get("brand"),
        "latitude": latitude,
        "longitude": longitude,
        "capacity": tags.get("capacity"),
        "socket_type": tags.get("socket:type"),
        "socket_type2": tags.get("socket:type2"),
        "opening_hours": tags.get("opening_hours"),
        "access": tags.get("access"),
        "fee": tags.get("fee"),
        "website": tags.get("website"),
        "phone": tags.get("phone"),
    })

# -------------------------------------------------------
# 5. Convert to DataFrame
# -------------------------------------------------------
df = pd.DataFrame(stations)

# Remove records without coordinates
df = df.dropna(
    subset=["latitude", "longitude"]
)

# Remove duplicate coordinates
df = df.drop_duplicates(
    subset=["latitude", "longitude"]
)

# -------------------------------------------------------
# 6. Save CSV
# -------------------------------------------------------
output_file = "delhi_ev_charging_stations_osm.csv"

df.to_csv(
    output_file,
    index=False,
    encoding="utf-8"
)

# -------------------------------------------------------
# 7. Results
# -------------------------------------------------------
print("\nDownload completed!")
print(f"Charging stations found: {len(df)}")
print(f"Saved to: {output_file}")

print("\nFirst 10 charging stations:")
print(df.head(10))