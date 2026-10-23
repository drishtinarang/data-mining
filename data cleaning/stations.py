"""
================================================================================
  PAN-INDIA EV CHARGING STATIONS - FULL PREPROCESSING PIPELINE
================================================================================
"""

import os
import re
import numpy as np
import pandas as pd
from scipy import stats

# ---------------------------------------------------------------------------
# PATHS - FIXED
# ---------------------------------------------------------------------------
INPUT_FILE  = r"C:\Users\HP\data-mining\Stations\pan_india_ev_charging_stations_complete.csv"
OUTPUT_FILE = r"C:\Users\HP\data-mining\data cleaning\pan_india_ev_charging_stations_CLEAN.csv"

print(f"Reading from : {INPUT_FILE}")
print(f"Writing to   : {OUTPUT_FILE}")

# ---------------------------------------------------------------------------
# 1. LOAD DATA
# ---------------------------------------------------------------------------
print("=" * 70)
print("  EV CHARGING STATIONS - PREPROCESSING PIPELINE")
print("=" * 70)

df = pd.read_csv(INPUT_FILE, dtype=str)
print(f"\n[1] Loaded {len(df):,} rows x {len(df.columns)} columns")
print(f"    Columns : {list(df.columns)}")

df_raw_count = len(df)

# ---------------------------------------------------------------------------
# 2. GEOGRAPHIC CLEANING
# ---------------------------------------------------------------------------
print("\n[2] Geographic cleaning ...")

df['latitude']  = pd.to_numeric(df['latitude'],  errors='coerce')
df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')

missing = df[df['latitude'].isna() | df['longitude'].isna()]
print(f"    Dropping {len(missing)} rows with null lat/lon")
df = df.dropna(subset=['latitude', 'longitude'])

INDIA_LAT_MIN, INDIA_LAT_MAX = 6.5,  37.5
INDIA_LON_MIN, INDIA_LON_MAX = 68.0, 98.0

swapped_mask = (
    df['latitude'].between(INDIA_LON_MIN, INDIA_LON_MAX) &
    df['longitude'].between(INDIA_LAT_MIN, INDIA_LAT_MAX)
)
if swapped_mask.sum() > 0:
    print(f"    Swapping {swapped_mask.sum()} rows with reversed lat/lon")
    df.loc[swapped_mask, ['latitude', 'longitude']] = (
        df.loc[swapped_mask, ['longitude', 'latitude']].values
    )

zero_mask = (df['latitude'] == 0.0) & (df['longitude'] == 0.0)
print(f"    Dropping {zero_mask.sum()} rows with (0,0) coordinates")
df = df[~zero_mask]

out_of_bounds = ~(
    df['latitude'].between(INDIA_LAT_MIN, INDIA_LAT_MAX) &
    df['longitude'].between(INDIA_LON_MIN, INDIA_LON_MAX)
)
print(f"    Dropping {out_of_bounds.sum()} rows outside India bounding box")
df = df[~out_of_bounds].reset_index(drop=True)

df['latitude']  = df['latitude'].round(6)
df['longitude'] = df['longitude'].round(6)
print(f"    OK {len(df):,} rows remain after geographic cleaning")

# ---------------------------------------------------------------------------
# 3. STATE & CITY STANDARDISATION
# ---------------------------------------------------------------------------
print("\n[3] Standardising state & city names ...")

STATE_MAP = {
    'Nct Of Delhi': 'Delhi', 'New Delhi': 'Delhi', 'Nct Delhi': 'Delhi',
    'Delhi Ncr': 'Delhi', 'National Capital Territory Of Delhi': 'Delhi',
    'Bangalore': 'Karnataka', 'Bengaluru': 'Karnataka', 'Bangalore Urban': 'Karnataka',
    'State Of Karnataka': 'Karnataka', 'Ka': 'Karnataka',
    'State Of Maharashtra': 'Maharashtra', 'Mh': 'Maharashtra',
    'Mumbai': 'Maharashtra', 'Bombay': 'Maharashtra',
    'State Of Tamil Nadu': 'Tamil Nadu', 'Tamilnadu': 'Tamil Nadu', 'Tn': 'Tamil Nadu',
    'State Of Gujarat': 'Gujarat', 'Gj': 'Gujarat',
    'Telangana State': 'Telangana', 'T.s.': 'Telangana',
    'Andhra': 'Andhra Pradesh', 'Ap': 'Andhra Pradesh',
    'State Of Kerala': 'Kerala', 'Kl': 'Kerala',
    'State Of Rajasthan': 'Rajasthan', 'Rj': 'Rajasthan',
    'State Of Uttar Pradesh': 'Uttar Pradesh', 'Up': 'Uttar Pradesh',
    'State Of West Bengal': 'West Bengal', 'Wb': 'West Bengal',
    'State Of Punjab': 'Punjab', 'Pb': 'Punjab',
    'State Of Haryana': 'Haryana', 'Hr': 'Haryana',
    'State Of Madhya Pradesh': 'Madhya Pradesh', 'Mp': 'Madhya Pradesh',
    'J&K': 'Jammu and Kashmir', 'J & K': 'Jammu and Kashmir',
    'Jammu & Kashmir': 'Jammu and Kashmir',
    'Hp': 'Himachal Pradesh',
    'Uk': 'Uttarakhand', 'Uttaranchal': 'Uttarakhand',
    'Cg': 'Chhattisgarh', 'Jh': 'Jharkhand',
    'Od': 'Odisha', 'Orissa': 'Odisha',
    'Goa State': 'Goa', 'Pondicherry': 'Puducherry',
    'Assam State': 'Assam',
}

df['state'] = df['state'].astype(str).str.strip().str.title().replace(STATE_MAP)
df['city']  = df['city'].astype(str).str.strip().str.title()

CITY_MAP = {
    'Bangalore': 'Bengaluru', 'Blr': 'Bengaluru',
    'Bombay': 'Mumbai', 'Calcutta': 'Kolkata', 'Madras': 'Chennai',
    'Hyderabad - Secunderabad': 'Hyderabad', 'Secunderabad': 'Hyderabad',
    'Navi Mumbai': 'Thane / Navi Mumbai', 'Thane': 'Thane / Navi Mumbai',
    'Greater Noida': 'Noida / Greater Noida', 'Noida': 'Noida / Greater Noida',
    'Ernakulam': 'Kochi / Ernakulam',
}
df['city'] = df['city'].replace(CITY_MAP)

print(f"    OK {df['state'].nunique()} unique states")
print(f"    Top 5: {dict(df['state'].value_counts().head(5))}")

# ---------------------------------------------------------------------------
# 4. CONNECTOR TYPE STANDARDISATION
# ---------------------------------------------------------------------------
print("\n[4] Standardising connector types ...")

CONNECTOR_MAP = {
    r'ccs\s*(type\s*2|2|combo\s*2|combo2)?': 'CCS2',
    r'combined\s*charging\s*system\s*(type\s*2|2)?': 'CCS2',
    r'ccs2': 'CCS2',
    r'chademo|cha?de?mo': 'CHAdeMO',
    r'type\s*2\s*(mennekes|ac)?|iec\s*62196|mennekes': 'Type 2 AC',
    r'type\s*1\s*(j1772)?|j[\-]?1772|sae\s*j\s*1772': 'Type 1 AC',
    r'gb[/\\]?t\s*20234': 'GB/T DC',
    r'gb[/\\]?t\s*9': 'GB/T AC',
    r'gb[/\\]?t': 'GB/T',
    r'bharat\s*ac[-_]?001|bharat\s*ev': 'Bharat AC001',
    r'bharat\s*dc[-_]?001': 'Bharat DC001',
    r'3[\s-]*pin\s*(domestic)?|domestic\s*(plug)?|bs\s*1363': '3-Pin Domestic',
    r'tesla\s*(supercharger|proprietary)?': 'Tesla Proprietary',
    r'schuko': 'Schuko (EU)',
}

def standardise_connector(raw):
    if pd.isna(raw) or str(raw).strip() == '':
        return 'Unknown'
    parts = [p.strip() for p in str(raw).split(',')]
    canonical = []
    for part in parts:
        matched = False
        part_lower = part.lower()
        for pattern, canon in CONNECTOR_MAP.items():
            if re.search(pattern, part_lower):
                if canon not in canonical:
                    canonical.append(canon)
                matched = True
                break
        if not matched and part:
            canonical.append(part.strip().title())
    return ', '.join(canonical) if canonical else 'Unknown'

df['connector_types_raw'] = df['connector_types']
df['connector_types'] = df['connector_types'].apply(standardise_connector)
print("    OK Top connector types:")
print(df['connector_types'].str.split(', ').explode().value_counts().head(8).to_string(header=False))

# ---------------------------------------------------------------------------
# 5. POWER (kW) & CHARGER TYPE STANDARDISATION
# ---------------------------------------------------------------------------
print("\n[5] Standardising power ratings & charger types ...")

df['max_power_kw'] = pd.to_numeric(df['max_power_kw'], errors='coerce')

def classify_charger_speed(kw):
    if pd.isna(kw):      return 'Unknown'
    if kw <= 3.5:        return 'Slow AC (<=3.5 kW)'
    elif kw <= 7.4:      return 'Standard AC (<=7.4 kW)'
    elif kw <= 22.0:     return 'Fast AC (11-22 kW)'
    elif kw <= 60.0:     return 'DC Fast (25-60 kW)'
    else:                return 'Ultra-Fast DC (>60 kW)'

df['charger_speed_class'] = df['max_power_kw'].apply(classify_charger_speed)
df['charging_speed'] = df['charger_speed_class']

print("    OK Charger speed distribution:")
print(df['charging_speed'].value_counts().to_string())

# ---------------------------------------------------------------------------
# 6. OPERATOR NAME STANDARDISATION
# ---------------------------------------------------------------------------
print("\n[6] Standardising operator (CPO) names ...")

OPERATOR_MAP = {
    r'tata\s*power|tata\s*ev': 'Tata Power EV',
    r'statiq|greenvolt': 'Statiq',
    r'charge\s*zone|chargezone': 'ChargeZone',
    r'ather': 'Ather Energy',
    r'fortum|charge\s*&\s*drive': 'Fortum Charge & Drive',
    r'bpcl|bharat\s*petroleum': 'BPCL',
    r'hpcl|hindustan\s*petroleum': 'HPCL',
    r'iocl|indian\s*oil': 'IOCL',
    r'bescom': 'BESCOM (Karnataka DISCOM)',
    r'msedcl|mahavitaran': 'MSEDCL (Maharashtra DISCOM)',
    r'discom': 'State DISCOM',
    r'ola\s*electric': 'Ola Electric',
    r'kazam': 'Kazam EV',
    r'magenta|chargegrid': 'Magenta ChargeGrid',
    r'\bevcs\b': 'EVCS',
    r'volttic': 'Volttic',
    r'ev\s*motors?\b|\bevm\b': 'EV Motors India',
    r'plugzmart': 'Plugzmart',
    r'bolt\.?earth|plugngo': 'Bolt.Earth',
    r'\babb\b': 'ABB (Hardware)',
    r'independent|municipal|unknown|\(unknown': 'Independent / Municipal',
}

def standardise_operator(raw):
    if pd.isna(raw) or str(raw).strip() == '':
        return 'Independent / Municipal'
    raw_lower = str(raw).lower()
    for pattern, canon in OPERATOR_MAP.items():
        if re.search(pattern, raw_lower):
            return canon
    return str(raw).strip().title()

df['operator_raw'] = df['operator']
df['operator'] = df['operator'].apply(standardise_operator)
print("    OK Top 10 operators:")
print(df['operator'].value_counts().head(10).to_string())

# ---------------------------------------------------------------------------
# 7. USAGE COST / PRICING PARSING
# ---------------------------------------------------------------------------
print("\n[7] Parsing usage cost / pricing ...")

def parse_cost(raw_cost):
    if pd.isna(raw_cost) or str(raw_cost).strip().lower() in ['unknown', 'nan', '', 'none']:
        return np.nan, 'Unknown', 'Unknown'
    raw = str(raw_cost).strip()
    if re.search(r'\bfree\b|\bno\s*charge\b|\bgratis\b', raw.lower()):
        return 0.0, 'Free', 'Free'
    number_match = re.search(r'[\d]+\.?[\d]*', raw)
    num = float(number_match.group()) if number_match else np.nan
    if   re.search(r'/\s*kwh|per\s*kwh', raw.lower()): unit = 'Rs/kWh'
    elif re.search(r'/\s*min|per\s*min', raw.lower()): unit = 'Rs/min'
    elif re.search(r'/\s*hr|per\s*hour', raw.lower()): unit = 'Rs/hr'
    elif re.search(r'/\s*session',       raw.lower()): unit = 'Rs/session'
    else: unit = 'Rs (unit unclear)'
    return num, unit, raw

cost_parsed            = df['usage_cost'].apply(parse_cost)
df['cost_numeric']     = [x[0] for x in cost_parsed]
df['cost_unit']        = [x[1] for x in cost_parsed]
df['usage_cost_clean'] = [x[2] for x in cost_parsed]

n = df['cost_numeric'].notna().sum()
print(f"    OK Parsed numeric cost for {n} / {len(df)} stations")

# ---------------------------------------------------------------------------
# 8. OPERATIONAL STATUS ENCODING
# ---------------------------------------------------------------------------
print("\n[8] Encoding operational status ...")

def parse_operational(val):
    if pd.isna(val): return True
    if str(val).lower() in ['true', '1', 'yes', 'operational']: return True
    if str(val).lower() in ['false', '0', 'no', 'closed']:      return False
    return True

df['is_operational'] = df['is_operational'].apply(parse_operational)
df['status_label']   = df['is_operational'].map({True: 'Operational', False: 'Non-Operational'})
print("    OK", df['status_label'].value_counts().to_dict())

# ---------------------------------------------------------------------------
# 9. OUTLIER DETECTION & HANDLING (IQR + Z-Score)
# ---------------------------------------------------------------------------
print("\n[9] Outlier detection ...")

df['total_ports'] = pd.to_numeric(df['total_ports'], errors='coerce').fillna(1).astype(int)

def iqr_bounds(series, multiplier=1.5):
    q1, q3 = series.quantile(0.25), series.quantile(0.75)
    iqr = q3 - q1
    return q1 - multiplier * iqr, q3 + multiplier * iqr

pow_lo, pow_hi = iqr_bounds(df['max_power_kw'].dropna())
df['max_power_kw_winsorized'] = df['max_power_kw'].clip(lower=max(0, pow_lo), upper=pow_hi)
df['power_is_outlier']        = (df['max_power_kw'] < pow_lo) | (df['max_power_kw'] > pow_hi)
print(f"    [Power kW]    IQR [{pow_lo:.1f}, {pow_hi:.1f}] -> {df['power_is_outlier'].sum()} outliers (winsorized)")

port_lo, port_hi = iqr_bounds(df['total_ports'].dropna())
df['total_ports_winsorized'] = df['total_ports'].clip(lower=1, upper=int(max(port_hi, 10)))
df['ports_is_outlier']       = (df['total_ports'] < port_lo) | (df['total_ports'] > port_hi)
print(f"    [Total Ports] IQR [{port_lo:.1f}, {port_hi:.1f}] -> {df['ports_is_outlier'].sum()} outliers (winsorized)")

cost_series = df['cost_numeric'].dropna()
if len(cost_series) > 10:
    cost_lo, cost_hi = iqr_bounds(cost_series)
    df['cost_is_outlier'] = df['cost_numeric'].apply(
        lambda x: bool(not pd.isna(x) and (x < cost_lo or x > cost_hi))
    )
    print(f"    [Cost Rs]     IQR [{cost_lo:.2f}, {cost_hi:.2f}] -> {df['cost_is_outlier'].sum()} outliers (flagged)")
else:
    df['cost_is_outlier'] = False

z_scores           = np.abs(stats.zscore(df['max_power_kw'].fillna(df['max_power_kw'].median())))
df['power_zscore'] = z_scores.round(3)
print(f"    [Z-Score]     {(z_scores > 3).sum()} rows with |Z| > 3 for max_power_kw")

# ---------------------------------------------------------------------------
# 10. FINAL CLEAN-UP & SAVE
# ---------------------------------------------------------------------------
print("\n[10] Final clean-up ...")

before = len(df)
df = df.drop_duplicates(subset=['station_id']).reset_index(drop=True)
print(f"    Deduplication: {before} -> {len(df)} rows")

df['latitude']       = df['latitude'].astype(float)
df['longitude']      = df['longitude'].astype(float)
df['max_power_kw']   = df['max_power_kw'].round(2)
df['total_ports']    = df['total_ports'].astype(int)
df['is_operational'] = df['is_operational'].astype(bool)
df['station_id']     = df['station_id'].astype(str)
df['pincode']        = df['pincode'].astype(str).str.strip().str.zfill(6)

FINAL_COLS = [
    'station_id', 'station_name',
    'state', 'city', 'address', 'pincode',
    'latitude', 'longitude',
    'operator',
    'charging_speed', 'charger_speed_class',
    'max_power_kw', 'max_power_kw_winsorized',
    'total_ports', 'total_ports_winsorized',
    'connector_types',
    'usage_cost_clean', 'cost_numeric', 'cost_unit',
    'is_operational', 'status_label',
    'power_is_outlier', 'ports_is_outlier', 'cost_is_outlier',
    'power_zscore',
    'connector_types_raw', 'operator_raw',
]
FINAL_COLS = [c for c in FINAL_COLS if c in df.columns]
df_clean = df[FINAL_COLS].copy()
df_clean.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')

# ---------------------------------------------------------------------------
# SUMMARY REPORT
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("  PREPROCESSING COMPLETE")
print("=" * 70)
print(f"  Input rows     : {df_raw_count:,}")
print(f"  Output rows    : {len(df_clean):,}")
print(f"  Rows removed   : {df_raw_count - len(df_clean):,}")
print(f"  Output columns : {len(df_clean.columns)}")
print(f"  Saved to       : {OUTPUT_FILE}")
print("=" * 70)

print("\nSTATIONS PER STATE:")
print(df_clean['state'].value_counts().to_string())

print("\nCHARGER SPEED CLASSES:")
print(df_clean['charger_speed_class'].value_counts().to_string())

print("\nTOP CONNECTOR TYPES:")
print(df_clean['connector_types'].value_counts().head(10).to_string())

print("\nTOP OPERATORS:")
print(df_clean['operator'].value_counts().head(12).to_string())

print("\nOUTLIER FLAGS:")
print(f"   Power outliers : {df_clean['power_is_outlier'].sum()}")
print(f"   Port outliers  : {df_clean['ports_is_outlier'].sum()}")
print(f"   Cost outliers  : {df_clean['cost_is_outlier'].sum()}")

print("\nSAMPLE ROWS (first 5):")
cols = ['station_name', 'state', 'city', 'operator', 'charger_speed_class', 'max_power_kw']
print(df_clean[cols].head(5).to_string(index=False))