import requests
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime

# =========================================================
# ⚠️ သင့် Database Password ကို ဒီမှာ ထည့်ပါ
DB_PASSWORD = 'root' 
engine = create_engine(f'postgresql://postgres:{DB_PASSWORD}@localhost:5432/agro_db')

# OpenWeather API Key (app.py ထဲက Key အတိုင်း)
API_KEY = '4f4a58051cf6cbea0fe0e181024354bc'
LAT, LON = 21.29, 99.60 # ကျိုင်းတုံမြို့

def update_weather_data():
    print(f"[{datetime.now()}] ရာသီဥတု Data အသစ် စတင်ဆွဲယူနေပါသည်...")
    
    # API မှ လာမည့် ၅ ရက်စာ (၃ နာရီတစ်ခါ) ခန့်မှန်းချက် ဆွဲယူခြင်း
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={LAT}&lon={LON}&appid={API_KEY}&units=metric"
    response = requests.get(url)
    data = response.json()

    if response.status_code != 200:
        print("❌ API မှ Data ဆွဲယူ၍ မရပါ။ Key သို့မဟုတ် Internet ကို စစ်ဆေးပါ။")
        return

    # Data များကို ရက်အလိုက် စုစည်းခြင်း
    daily_data = {}
    for item in data.get("list", []):
        date_str = item["dt_txt"][:10]
        temp = item["main"]["temp"]
        rain = item.get("rain", {}).get("3h", 0)

        if date_str not in daily_data:
            daily_data[date_str] = {"temp_sum": 0, "count": 0, "rain": 0}
        
        daily_data[date_str]["temp_sum"] += temp
        daily_data[date_str]["count"] += 1
        daily_data[date_str]["rain"] += rain

    # 👇 ဒီကုဒ်လေး ထပ်ထည့်ပါ (အနုတ်ကိန်းတွေ မဝင်အောင် ကာကွယ်ဖို့)
    for d in daily_data:
        if daily_data[d]["rain"] < 0:
            daily_data[d]["rain"] = 0

    # Database ထဲသို့ ထည့်ခြင်း
    with engine.begin() as conn:
        for date_str, values in daily_data.items():
            avg_temp = values["temp_sum"] / values["count"]
            total_rain = values["rain"]
            # မိုးရေချိန် အနုတ်ကိန်း မဖြစ်စေရန် ကာကွယ်ခြင်း
            if total_rain < 0: total_rain = 0

            # ရက်စွဲ ရှိပြီးသားလား စစ်ဆေးပြီး မရှိမှ ထည့်မည် (သို့) ရှိရင် Update လုပ်မည်
            check_query = text("SELECT date FROM weather_data WHERE date = :d")
            existing = conn.execute(check_query, {"d": date_str}).fetchone()

            if existing:
                update_query = text("""
                    UPDATE weather_data 
                    SET "T2M" = :t, "PRECTOTCORR" = :r 
                    WHERE date = :d
                """)
                conn.execute(update_query, {"t": avg_temp, "r": total_rain, "d": date_str})
            else:
                insert_query = text("""
                    INSERT INTO weather_data (date, "T2M", "PRECTOTCORR") 
                    VALUES (:d, :t, :r)
                """)
                conn.execute(insert_query, {"d": date_str, "t": avg_temp, "r": total_rain})
            
    print(f"[{datetime.now()}] ✅ ရက်စွဲ {len(daily_data)} ရက်စာ Data များကို Database ထဲသို့ အောင်မြင်စွာ ထည့်သွင်းပြီးပါပြီ။")
def cleanup_bad_dates():
    with engine.begin() as conn:
        # ✅ အသစ်ပြင်ဆင်ထားသော ကုဒ် (date::text ဖြင့် စာသားအဖြစ် ပြောင်းပြီး စစ်ဆေးခြင်း)
        conn.execute(text("DELETE FROM weather_data WHERE date::text !~ '^\\d{4}-\\d{2}-\\d{2}$'"))
    print("🧹 ရက်စွဲဖော်မတ် မှားနေတဲ့ row တွေ ရှင်းပြီးပါပြီ။")

# update_weather_data() ခေါ်ပြီးနောက် (သို့) __main__ မှာ ခေါ်ပါ
if __name__ == "__main__":
    update_weather_data()
    cleanup_bad_dates()
    
if __name__ == "__main__":
    update_weather_data()