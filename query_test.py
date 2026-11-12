import pandas as pd
from sqlalchemy import create_engine, text

# ⚠️ သင့် PostgreSQL Password ကို ထည့်ပါ
DB_PASSWORD = 'root'  
DB_NAME = 'agro_db'
DB_USER = 'postgres'
DB_HOST = 'localhost'
DB_PORT = '5432'

engine = create_engine(f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

def run_query(title, query):
    print(f"\n{'='*50}")
    print(f"📌 {title}")
    print(f"{'='*50}")
    try:
        df = pd.read_sql(text(query), engine)
        print(df.to_string(index=False))
    except Exception as e:
        print(f"❌ Error: {e}")

# ---------------------------------------------------------
# Query 1: Spatial Query (PostGIS - အကွာအဝေးကို Numeric ပြောင်းပြီး တွက်မယ်)
# ---------------------------------------------------------
q1 = """
SELECT 
    f.farm_id, 
    f.farm_name, 
    s.station_name AS nearest_station,
    ROUND(CAST(
        ST_Distance(
            ST_SetSRID(ST_MakePoint(f.longitude, f.latitude), 4326)::geography,
            ST_SetSRID(ST_MakePoint(s.longitude, s.latitude), 4326)::geography
        ) / 1000.0 AS numeric
    ), 2) AS distance_km
FROM farms f
CROSS JOIN LATERAL (
    SELECT station_name, latitude, longitude
    FROM weather_stations
    ORDER BY ST_SetSRID(ST_MakePoint(f.longitude, f.latitude), 4326)::geography <-> ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography
    LIMIT 1
) s
WHERE f.farm_id IN ('F003', 'F013', 'F001'); 
"""
run_query("Query 1: Spatial Query (အနီးဆုံးစခန်းရှာခြင်း)", q1)

# ---------------------------------------------------------
# Query 2: Window Function (၇ ရက်တာ မိုးရေချိန် ပျမ်းမျှ)
# ---------------------------------------------------------
q2 = """
SELECT 
    date::text, 
    "PRECTOTCORR" AS rainfall_mm,
    ROUND(AVG("PRECTOTCORR") OVER (
        ORDER BY date::text 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    )::numeric, 2) AS moving_avg_7d
FROM weather_data
WHERE date::text >= '20240601' AND date::text <= '20240615'
ORDER BY date::text;
"""
run_query("Query 2: Window Function (၇ ရက်တာ မိုးရေချိန် ပျမ်းမျှ)", q2)

# ---------------------------------------------------------
# Query 3: သီးနှံအလိုက် စိုက်ခင်း အရေအတွက် (Group By)
# ---------------------------------------------------------
q3 = """
SELECT 
    current_crop AS crop_type, 
    COUNT(*) AS number_of_farms
FROM farms
GROUP BY current_crop
ORDER BY number_of_farms DESC;
"""
run_query("Query 3: သီးနှံအလိုက် စိုက်ခင်း အရေအတွက် (Group By)", q3)

# ---------------------------------------------------------
# Query 4: အမြင့် ၂၅၀၀ ကျော် လက်ဖက်ခြံများ (Rule-based Filter)
# ---------------------------------------------------------
q4 = """
SELECT 
    farm_id, 
    farm_name, 
    elevation_m, 
    current_crop
FROM farms
WHERE current_crop LIKE '%%Tea%%' 
  AND elevation_m >= 2500;
"""
run_query("Query 4: အမြင့် ၂၅၀၀ ကျော် လက်ဖက်ခြံများ (Rule-based Filter)", q4)