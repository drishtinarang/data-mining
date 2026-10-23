[1] Loaded 1,980 rows x 15 columns
    Columns : ['station_id', 'station_name', 'state', 'city', 'address', 'pincode', 'latitude', 'longitude', 'operator', 'charging_speed', 'max_power_kw', 'total_ports', 'connector_types', 'usage_cost', 'is_operational']

[2] Geographic cleaning ...
    Dropping 0 rows with null lat/lon
    Dropping 0 rows with (0,0) coordinates
    Dropping 0 rows outside India bounding box
    OK 1,980 rows remain after geographic cleaning

[3] Standardising state & city names ...
    OK 37 unique states
    Top 5: {'Kerala': np.int64(595), 'Karnataka': np.int64(388), 'Odisha': np.int64(370), 'Tamil Nadu': np.int64(228), 'Maharashtra': np.int64(85)}

[4] Standardising connector types ...
    OK Top connector types:
CCS2              1511
Type 2 AC          345
Unknown            261
3-Pin Domestic     167
CHAdeMO             73
GB/T DC             44
Type M               8
Type 1 AC            4

[5] Standardising power ratings & charger types ...
    OK Charger speed distribution:
charging_speed
DC Fast (25-60 kW)        1323
Standard AC (<=7.4 kW)     238
Ultra-Fast DC (>60 kW)     203
Slow AC (<=3.5 kW)         160
Fast AC (11-22 kW)          56

[6] Standardising operator (CPO) names ...
    OK Top 10 operators:
operator
Independent / Municipal    612
Chargemod (In)             292
Go Ec (In)                 185
Tata Power EV              175
Zeon Charging              172
ChargeZone                 146
Statiq                     125
Jio Bp Pulse (India)        81
Relux Electric (India)      37
Shell Recharge (In)         34

[7] Parsing usage cost / pricing ...
    OK Parsed numeric cost for 1105 / 1980 stations

[8] Encoding operational status ...
    OK {'Operational': 1943, 'Non-Operational': 37}

[9] Outlier detection ...
    [Power kW]    IQR [-30.0, 114.0] -> 110 outliers (winsorized)
    [Total Ports] IQR [-0.5, 3.5] -> 209 outliers (winsorized)
    [Cost Rs]     IQR [14.00, 30.00] -> 39 outliers (flagged)
    [Z-Score]     1 rows with |Z| > 3 for max_power_kw

[10] Final clean-up ...
    Deduplication: 1980 -> 1980 rows

======================================================================
  PREPROCESSING COMPLETE
======================================================================
  Input rows     : 1,980
  Output rows    : 1,980
  Rows removed   : 0
  Output columns : 27
  Saved to       : C:\Users\HP\data-mining\data cleaning\pan_india_ev_charging_stations_CLEAN.csv
======================================================================

STATIONS PER STATE:
state
Kerala                    595
Karnataka                 388
Odisha                    370
Tamil Nadu                228
Maharashtra                85
Gujarat                    67
Rajasthan                  50
Uttar Pradesh              32
Delhi                      32
Haryana                    28
Telangana                  19
Uttarakhand                12
Madhya Pradesh             11
Andhra Pradesh             10
West Bengal                 9
Goa                         7
Keral                       4
Puducherry                  3
Himachal Pradesh            3
Dadra And Nagar Haveli      3
Ahmedabad                   2
Maharshtra                  2
Mahrashtra                  2
Assam                       2
Uttarakhnad                 2
Jharkhand                   2
Punjab                      2
Burari                      1
Jammu And Kashmir           1
New Dehi                    1
Keraka                      1
Lerala                      1
Karnatak                    1
Villupuram                  1
Chennai                     1
India                       1
Bihar                       1

CHARGER SPEED CLASSES:
charger_speed_class
DC Fast (25-60 kW)        1323
Standard AC (<=7.4 kW)     238
Ultra-Fast DC (>60 kW)     203
Slow AC (<=3.5 kW)         160
Fast AC (11-22 kW)          56

TOP CONNECTOR TYPES:
connector_types
CCS2                                 1188
Unknown                               245
Type 2 AC                             195
CCS2, 3-Pin Domestic                  111
CCS2, Type 2 AC                        79
CCS2, CHAdeMO                          31
CCS2, CHAdeMO, Type 2 AC               20
CCS2, 3-Pin Domestic, Type 2 AC        18
CCS2, CHAdeMO, GB/T DC, Type 2 AC      16
CCS2, Unknown                          14

TOP OPERATORS:
operator
Independent / Municipal    612
Chargemod (In)             292
Go Ec (In)                 185
Tata Power EV              175
Zeon Charging              172
ChargeZone                 146
Statiq                     125
Jio Bp Pulse (India)        81
Relux Electric (India)      37
Shell Recharge (In)         34
Salzer Nexcharge (In)       23
Eesl (In)                   22

OUTLIER FLAGS:
   Power outliers : 110
   Port outliers  : 209
   Cost outliers  : 39

SAMPLE ROWS (first 5):
                            station_name            state        city                operator    charger_speed_class  max_power_kw
          Fleettrack Telematic Solutions       Tamil Nadu  Coimbatore   Salzer Nexcharge (In) Standard AC (<=7.4 kW)           7.0
                        Drise EV Charger       Puducherry  Puducherry   Salzer Nexcharge (In)     DC Fast (25-60 kW)          60.0
                              khuurampur    Uttar Pradesh  Muradnagar Independent / Municipal     Slow AC (<=3.5 kW)           3.3
        E-Fill Electric Hotel Food Mania Himachal Pradesh Balh, Mandi    E-Fill Electric (In)     DC Fast (25-60 kW)          30.0
Nilkanth EV Charging Station - ChargeJet          Gujarat   Ahemdabad Independent / Municipal Ultra-Fast DC (>60 kW)         158.0
PS C:\Users\HP\data-mining> 