import pandas as pd
from sqlalchemy import create_engine, text
import os
from werkzeug.security import generate_password_hash

DB_PASSWORD = 'root'  # ⚠️ သင့် Password ကို ထည့်ပါ
DB_NAME = 'agro_db'
DB_USER = 'postgres'
DB_HOST = 'localhost'
DB_PORT = '5432'

engine = create_engine(f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

print("📡 Database နဲ့ ချိတ်ဆက်နေသည်...")
try:
    with engine.connect() as conn:
        print("✅ Database ချိတ်ဆက်မှု အောင်မြင်ပါသည်။")
except Exception as e:
    print(f"❌ ချိတ်ဆက်မှု မအောင်မြင်ပါ။ Password ကို ပြန်စစ်ပါ။ Error: {e}")
    exit()

print("\n⏳ Data များ ထည့်သွင်းနေသည်...")

# =======================================================
# 1. ပင်မ Data များ ထည့်သွင်းခြင်း
# =======================================================
try:
    df_farms = pd.read_csv('data/farms_locations.csv')
    df_stations = pd.read_csv('data/weather_stations.csv')
    df_crops = pd.read_csv('data/Crop_recommendation.csv')
    df_guides = pd.read_csv('data/crop_guides.csv', encoding='utf-8-sig')

    df_farms.to_sql('farms', engine, if_exists='replace', index=False)
    df_stations.to_sql('weather_stations', engine, if_exists='replace', index=False)
    df_crops.to_sql('crop_recommendation', engine, if_exists='replace', index=False)
    df_guides.to_sql('crop_guides', engine, if_exists='replace', index=False)
    
    print("✅ ပင်မ Data များ ထည့်သွင်းပြီးပါပြီ။")
except Exception as e:
    print(f"⚠️ ပင်မ Data ထည့်ရာတွင် Error: {e}")

# =======================================================
# 2. ရာသီဥတု Data (weather_data) ထည့်သွင်းခြင်း (ဂရုတစိုက်)
# =======================================================
print("\n⏳ ရာသီဥတု Data များ ထည့်သွင်းနေသည်...")
try:
    df_weather = pd.read_csv('data/weather_kengtung_2020_2024.csv')
    
    # ရက်စွဲကော်လံကို စာသား (String) အဖြစ် သေချာအောင် ပြောင်းမယ်
    if 'date' in df_weather.columns:
        df_weather['date'] = df_weather['date'].astype(str)

    # Table ရှိပြီးသားလား စစ်မယ်
    with engine.connect() as conn:
        table_exists = conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'weather_data')")).scalar()

    if not table_exists:
        # Table မရှိသေးရင် အသစ်ဆောက်ပြီး ထည့်မယ်
        df_weather.to_sql('weather_data', engine, if_exists='replace', index=False)
        print("✅ ရာသီဥတု Table အသစ် ဆောက်ပြီး Data ထည့်ပြီးပါပြီ။")
    else:
        # Table ရှိပြီးသားဆိုရင် ရက်စွဲကော်လံကို Text အဖြစ် အတင်းပြောင်းမယ် (Error မတက်အောင်)
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE weather_data ALTER COLUMN date TYPE VARCHAR(20);"))
        
        # Data တွေ ထပ်တိုးမယ် (အဟောင်းတွေ မဖျက်ဘူး)
        df_weather.to_sql('weather_data', engine, if_exists='append', index=False)
        print("✅ ရာသီဥတု Data များကို ထပ်တိုး ထည့်သွင်းပြီးပါပြီ။")
except Exception as e:
    print(f"⚠️ ရာသီဥတု Data ထည့်ရာတွင် Error: {e}")

# =======================================================
# 3. စျေးနှုန်း Data ထည့်သွင်းခြင်း
# =======================================================
print("\n⏳ သီးနှံစျေးနှုန်း Data များ ထည့်သွင်းနေသည်...")
try:
    df_prices = pd.read_csv('data/crop_prices.csv', encoding='utf-8-sig')
    df_prices.to_sql('crop_prices', engine, if_exists='replace', index=False)
    print(f"✅ သီးနှံစျေးနှုန်း Data {len(df_prices)} ခုကို 'crop_prices' Table ထဲ ထည့်ပြီးပါပြီ။")
except Exception as e:
    print(f"⚠️ စျေးနှုန်း Data ထည့်ရာတွင် Error: {e}")

# =======================================================
# 4. Chatbot အတွက် အသစ်ထည့်မယ့် အပိုင်း
# =======================================================
print("\n⏳ Chatbot Dataset ကို ထည့်သွင်းနေသည်...")
try:
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS crop_dataset (
                id SERIAL PRIMARY KEY,
                question TEXT NOT NULL,
                answer TEXT NOT NULL
            );
        """))
    
    df_chatbot = pd.read_csv('data/crop_data.csv', encoding='utf-8-sig')
    
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE crop_dataset RESTART IDENTITY;"))
    
    with engine.begin() as conn:
        for _, row in df_chatbot.iterrows():
            conn.execute(
                text("INSERT INTO crop_dataset (question, answer) VALUES (:q, :a)"),
                {"q": row['Question'], "a": row['Answer']}
            )
    print(f"✅ Chatbot အတွက် မေးခွန်း-အဖြေ {len(df_chatbot)} ခုကို ထည့်သွင်းပြီးပါပြီ။")
except Exception as e:
    print(f"⚠️ Chatbot Dataset ထည့်ရာတွင် Error: {e}")

# =======================================================
# 5. User Account နဲ့ Chat History အတွက် Table အသစ်များ ဆောက်ခြင်း
# =======================================================
print("\n⏳ User နှင့် Chat History Table များ ဆောက်နေသည်...")
with engine.begin() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            role VARCHAR(10) DEFAULT 'user'
        );
    """))
    
    conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(10) DEFAULT 'user';"))
    
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id SERIAL PRIMARY KEY,
            user_id INT REFERENCES users(id),
            user_message TEXT,
            bot_response TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """))
print("✅ User နှင့် Chat History Table များ ဆောက်ပြီးပါပြီ။")

# =======================================================
# 6. Admin Account ဖန်တီးခြင်း
# =======================================================
print("\n⏳ Admin Account ဖန်တီးနေသည်...")
try:
    admin_pw = generate_password_hash('admin123')
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO users (username, password, role) 
            VALUES ('admin', :pw, 'admin')
            ON CONFLICT (username) DO UPDATE SET role = 'admin';
        """), {"pw": admin_pw})
    print("✅ Admin Account ဖန်တီးပြီးပါပြီ။ (username: admin, password: admin123)")
except Exception as e:
    print(f"⚠️ Admin Account ဖန်တီးရာတွင် Error: {e}")

# =======================================================
# 7. Crop Parameters Table ဆောက်ခြင်း
# =======================================================
print("\n⏳ Crop Parameters Data များ ထည့်သွင်းနေသည်...")
try:
    df_params = pd.read_csv('data/crop_params.csv', encoding='utf-8-sig')
    df_params.to_sql('crop_params', engine, if_exists='replace', index=False)
    print(f"✅ သီးနှံ {len(df_params)} မျိုးအတွက် Parameter Data များ ထည့်သွင်းပြီးပါပြီ။")
except Exception as e:
    print(f"⚠️ Crop Parameters ထည့်ရာတွင် Error: {e}")

# =======================================================
# 8. စျေးနှုန်းမှတ်တမ်း (price_history) Table ဆောက်ခြင်း (အသစ်ပြင်ဆင်ထားသည်)
# =======================================================
print("\n⏳ စျေးနှုန်းမှတ်တမ်း (price_history) Table ဆောက်နေသည်...")
try:
    with engine.begin() as conn:
        # Table ရှိပြီးသားလား စစ်မယ်
        table_exists = conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'price_history')")).scalar()
        
        if not table_exists:
            # Table မရှိသေးရင် အသစ်ဆောက်မယ် (recorded_date ပါဝင်သည်)
            conn.execute(text("""
                CREATE TABLE price_history (
                    id SERIAL PRIMARY KEY,
                    crop_name VARCHAR(50) NOT NULL,
                    min_price INT NOT NULL,
                    max_price INT NOT NULL,
                    recorded_date DATE DEFAULT CURRENT_DATE,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            print("✅ စျေးနှုန်းမှတ်တမ်း Table အသစ် ဆောက်ပြီးပါပြီ။")
        else:
            # Table ရှိပြီးသားဆိုရင် recorded_date ကော်လံ ရှိမရှိ စစ်မယ်
            column_exists = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'price_history' AND column_name = 'recorded_date'
                )
            """)).scalar()
            
            if not column_exists:
                # recorded_date မရှိရင် ထပ်ထည့်မယ်
                conn.execute(text("ALTER TABLE price_history ADD COLUMN recorded_date DATE DEFAULT CURRENT_DATE;"))
                print("✅ စျေးနှုန်းမှတ်တမ်း Table ထဲကို recorded_date ကော်လံ ထပ်ထည့်ပြီးပါပြီ။")
            else:
                print("✅ စျေးနှုန်းမှတ်တမ်း Table ရှိပြီးသားဖြစ်ပါသည်။")
except Exception as e:
    print(f"⚠️ Error: {e}")

# =======================================================
# 9. Alert Subscriptions Table ဆောက်ခြင်း
# =======================================================
print("\n⏳ Alert Subscription Table ဆောက်နေသည်...")
try:
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS alert_subscriptions (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) NOT NULL,
                farm_id VARCHAR(20) NOT NULL,
                last_sent_date VARCHAR(10) DEFAULT '',
                UNIQUE(email, farm_id)
            );
        """))
    print("✅ Alert Subscription Table ဆောက်ပြီးပါပြီ။")
except Exception as e:
    print(f"⚠️ Error: {e}")

# =======================================================
# 10. PDF ဖိုင်များ သိမ်းဆည်းရန် Table ဆောက်ခြင်း
# =======================================================
print("\n⏳ PDF ဖိုင်များ သိမ်းဆည်းရန် Table ဆောက်နေသည်...")
try:
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS crop_pdfs (
                id SERIAL PRIMARY KEY,
                crop_name VARCHAR(100) NOT NULL,
                pdf_filename VARCHAR(255) NOT NULL,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
    print("✅ PDF ဖိုင်များ သိမ်းဆည်းရန် Table ဆောက်ပြီးပါပြီ။")
except Exception as e:
    print(f"⚠️ Error: {e}")

# =======================================================
# 11. မြေအမျိုးအစားနှင့် သီးနှံ ဆက်စပ်မှု Table ဆောက်ခြင်း
# =======================================================
print("\n⏳ မြေအမျိုးအစားနှင့် သီးနှံ ဆက်စပ်မှု Table ဆောက်နေသည်...")
try:
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS soil_crop_mapping (
                id SERIAL PRIMARY KEY,
                soil_type VARCHAR(100) NOT NULL,
                recommended_crops TEXT NOT NULL
            );
        """))
        
        # ရှိပြီးသား Data တွေ ရှိရင် အရင်ရှင်းမယ်
        conn.execute(text("TRUNCATE TABLE soil_crop_mapping RESTART IDENTITY;"))
        
        # မြေအမျိုးအစားအလိုက် သီးနှံတွေ ထည့်မယ်
        conn.execute(text("""
            INSERT INTO soil_crop_mapping (soil_type, recommended_crops) VALUES
            ('Meadow & Meadow Alluvial Soils', 'စပါး, ဟင်းသီးဟင်းရွက်, ပြောင်း, ဖရဲသီး, ပဲပုပ်'),
            ('Gley & Gley Swampy Soils', 'စပါး, ဖရဲသီး'),
            ('Red Brown Forest Soils', 'လက်ဖက်, ကော်ဖီ, သစ်သီးဝလံ'),
            ('Yellow Brown Forest Soils', 'လက်ဖက်, ကော်ဖီ, ပြောင်း'),
            ('Red Earths & Yellow Earths', 'ပြောင်း, ပဲပုပ်, လက်ဖက်, ကော်ဖီ, စတော်ဘယ်ရီ'),
            ('Mountainous Brown Forest Soils', 'လက်ဖက်, ကော်ဖီ'),
            ('Mountainous Red Forest Soils', 'လက်ဖက်, ကော်ဖီ, သစ်သီးဝလံ'),
            ('Alluvial', 'စပါး, ပြောင်း, ဖရဲသီး'),
            ('Lateritic', 'လက်ဖက်, ကော်ဖီ, ရော်ဘာ, နာနတ်သီး');
        """))
    print("✅ မြေအမျိုးအစားနှင့် သီးနှံ ဆက်စပ်မှု Table ဆောက်ပြီးပါပြီ။")
except Exception as e:
    print(f"⚠️ Error: {e}")

# =======================================================
# 12. Database အတွင်းရှိ Data အရေအတွက်ကို ပြမယ်
# =======================================================
print("\n📊 Database အတွင်းရှိ အချက်အလက်များ -")
with engine.connect() as conn:
    tables = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")).fetchall()
    for table in tables:
        table_name = table[0]
        count = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
        print(f"  - Table '{table_name}' တွင် Data {count} ခု ရှိပါသည်။")

print("\n🎉 အားလုံး ပြီးစီးပါပြီ!")