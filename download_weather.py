import requests
import pandas as pd
import os
from datetime import datetime

lat = 21.29
lon = 99.61
start = "20200101"
end = datetime.now().strftime("%Y%m%d")   # ← ဒီနေ့အထိ

url = "https://power.larc.nasa.gov/api/temporal/daily/point"
params = {
    "parameters": "T2M,PRECTOTCORR,RH2M",
    "community": "AG",
    "longitude": lon, "latitude": lat,
    "start": start, "end": end, "format": "JSON"
}

response = requests.get(url, params=params, timeout=60)
data = response.json()
df = pd.DataFrame(data['properties']['parameter'])
df.index.name = 'date'
os.makedirs('data', exist_ok=True)
df.to_csv('data/weather_kengtung_2020_2024.csv')
print(f"✅ Updated {len(df)} rows, last date: {df.index[-1]}")