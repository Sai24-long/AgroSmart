import requests
import smtplib
import re
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request, session, redirect, url_for, render_template_string
from sqlalchemy import create_engine, text
import pandas as pd
import joblib
import math
from openai import OpenAI
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# Static folder ကို သတ်မှတ်ပေးရပါမယ် (ပုံတွေအတွက်)
app = Flask(__name__, static_folder='static', static_url_path='/static')
import db_setup.py
# Session အတွက် လျှို့ဝှက်ကုဒ် (Login အတွက် မဖြစ်မနေ လိုပါတယ်)
app.secret_key = 'agrosmart_kengtung_secret_key_2026'

# =========================================================
# ⚠️ သင့် PostgreSQL Password ကို ဒီမှာ ထည့်ပါ
DB_PASSWORD = 'root'
# =========================================================

engine = create_engine(f'postgresql://postgres:{DB_PASSWORD}@localhost:5432/agro_db')

# =========================================================
# 📧 Email Subscription Table (auto-create)
# =========================================================
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
except Exception as e:
    print(f"⚠️ Subscription table မဆောက်နိုင်ပါ: {e}")

# 📄 PDF ဖိုင်များ သိမ်းဆည်းရန် Folder ဆောက်ခြင်း
PDF_FOLDER = os.path.join('static', 'pdfs')
os.makedirs(PDF_FOLDER, exist_ok=True)

# ⚠️ Gmail နဲ့ ပို့ချင်ရင် — 2FA on လုပ်ပြီး App Password ယူပါ
SMTP_EMAIL = 'saiwoonc@gmail.com'
SMTP_PASSWORD = 'homg djqq cqay bebz'

try:
    model = joblib.load('crop_model.pkl')
except:
    model = None

# =========================================================
# 🎨 UI Templates (Agriculture Theme Design)
# =========================================================
LOGIN_HTML = """
<!DOCTYPE html>
<html lang="my">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login | AgroSmart Kengtung</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Padauk:wght@400;700&display=swap" rel="stylesheet">
    <script>
        tailwind.config = {
            theme: { extend: { colors: { brand: { 500: '#10b981', 600: '#059669', 700: '#047857' } }, fontFamily: { sans: ['Padauk', 'sans-serif'] } } }
        }
    </script>
    <style>
        body {
            font-family: 'Padauk', sans-serif;
            background-image: linear-gradient(rgba(0, 0, 0, 0.4), rgba(0, 0, 0, 0.6)), url('https://images.unsplash.com/photo-1500382017468-9049fed747ef?q=80&w=2000&auto=format&fit=crop');
            background-size: cover; background-position: center;
        }
    </style>
</head>
<body class="h-screen flex items-center justify-center p-4">
    <div class="bg-white/95 backdrop-blur-md p-8 rounded-3xl shadow-2xl w-full max-w-md border border-white/20">
        <div class="text-center mb-8">
            <div class="w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-4 shadow-inner">
                <svg class="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"></path></svg>
            </div>
            <h1 class="text-3xl font-extrabold text-green-700 mb-2">AgroSmart Kengtung</h1>
            <p class="text-gray-500 font-medium">စိုက်ပျိုးရေး စနစ်သို့ ဝင်ရောက်ရန်</p>
        </div>
        
        {% if error %}
        <div class="bg-red-50 text-red-600 p-3 rounded-xl mb-6 text-sm font-semibold text-center border border-red-100">{{ error }}</div>
        {% endif %}

        <form method="POST" class="space-y-5">
            <div>
                <label class="block text-sm font-bold text-gray-700 mb-1">အသုံးပြုသူအမည် (Username)</label>
                <input type="text" name="username" required placeholder="ဥပမာ - aung123"
                    class="w-full px-4 py-3 bg-gray-50 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-green-500 text-gray-800">
            </div>
            <div>
                <label class="block text-sm font-bold text-gray-700 mb-1">စကားဝှက် (Password)</label>
                <input type="password" name="password" required placeholder="••••••••"
                    class="w-full px-4 py-3 bg-gray-50 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-green-500 text-gray-800">
            </div>
            <button type="submit" class="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 rounded-xl shadow-lg transition duration-300 transform hover:-translate-y-0.5">
                Login ဝင်ရောက်မည်
            </button>
        </form>
        
        <p class="text-center text-sm text-gray-500 mt-6">
            အကောင့်မရှိသေးဘူးလား? <a href="/signup" class="text-green-600 font-bold hover:underline">အကောင့်အသစ်ဖွင့်ရန်</a>
        </p>
        <div class="text-center mt-4">
            <a href="/" class="text-sm text-gray-500 hover:text-green-600 transition">⬅ Dashboard သို့ ပြန်သွားရန်</a>
        </div>
    </div>
</body>
</html>
"""

SIGNUP_HTML = """
<!DOCTYPE html>
<html lang="my">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sign Up | AgroSmart Kengtung</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Padauk:wght@400;700&display=swap" rel="stylesheet">
    <script>
        tailwind.config = {
            theme: { extend: { colors: { brand: { 500: '#10b981', 600: '#059669', 700: '#047857' } }, fontFamily: { sans: ['Padauk', 'sans-serif'] } } }
        }
    </script>
    <style>
        body {
            font-family: 'Padauk', sans-serif;
            background-image: linear-gradient(rgba(0, 0, 0, 0.3), rgba(0, 0, 0, 0.6)), url('https://images.unsplash.com/photo-1625246333195-78d9c38ad449?q=80&w=2000&auto=format&fit=crop');
            background-size: cover; background-position: center;
        }
    </style>
</head>
<body class="h-screen flex items-center justify-center p-4">
    <div class="bg-white/95 backdrop-blur-md p-8 rounded-3xl shadow-2xl w-full max-w-md border border-white/20">
        <div class="text-center mb-8">
            <div class="w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-4 shadow-inner">
                <svg class="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"></path></svg>
            </div>
            <h1 class="text-3xl font-extrabold text-green-700 mb-2">အကောင့်အသစ်ဖွင့်ရန်</h1>
            <p class="text-gray-500 font-medium">AgroSmart မှ ကြိုဆိုပါတယ်</p>
        </div>
        
        {% if error %}
        <div class="bg-red-50 text-red-600 p-3 rounded-xl mb-6 text-sm font-semibold text-center border border-red-100">{{ error }}</div>
        {% endif %}

        <form method="POST" class="space-y-5">
            <div>
                <label class="block text-sm font-bold text-gray-700 mb-1">အသုံးပြုသူအမည် (Username)</label>
                <input type="text" name="username" required placeholder="အသုံးပြုမည့် အမည်"
                    class="w-full px-4 py-3 bg-gray-50 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-green-500 text-gray-800">
            </div>
            <div>
                <label class="block text-sm font-bold text-gray-700 mb-1">စကားဝှက် (Password)</label>
                <input type="password" name="password" required placeholder="လုံခြုံသော စကားဝှက်"
                    class="w-full px-4 py-3 bg-gray-50 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-green-500 text-gray-800">
            </div>
            <button type="submit" class="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 rounded-xl shadow-lg transition duration-300 transform hover:-translate-y-0.5">
                အကောင့်ဖွင့်မည်
            </button>
        </form>
        
        <p class="text-center text-sm text-gray-500 mt-6">
            အကောင့်ရှိပြီးသားလား? <a href="/login" class="text-green-600 font-bold hover:underline">Login ဝင်ရောက်ရန်</a>
        </p>
        <div class="text-center mt-4">
            <a href="/" class="text-sm text-gray-500 hover:text-green-600 transition">⬅ Dashboard သို့ ပြန်သွားရန်</a>
        </div>
    </div>
</body>
</html>
"""

# =========================================================
# 👤 Login / Signup Routes
# =========================================================
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_pw = generate_password_hash(password)
        
        try:
            with engine.begin() as conn:
                conn.execute(text("INSERT INTO users (username, password, role) VALUES (:u, :p, 'user')"),
                             {"u": username, "p": hashed_pw})
            return redirect('/login')
        except Exception as e:
            error_msg = "❌ အဲ့ဒီ Username ကို အသုံးပြုပြီးသား ဖြစ်နေပါတယ်။"
            return render_template_string(SIGNUP_HTML, error=error_msg)
            
    return render_template_string(SIGNUP_HTML, error=None)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        df_user = pd.read_sql(f"SELECT * FROM users WHERE username = '{username}'", engine)
        if not df_user.empty:
            if check_password_hash(df_user.iloc[0]['password'], password):
                session['user_id'] = int(df_user.iloc[0]['id'])
                session['username'] = username
                session['role'] = df_user.iloc[0]['role']
                
                if session['role'] == 'admin':
                    return redirect('/admin')
                return redirect('/chatbot_similarity')
        
        error_msg = "❌ Username သို့မဟုတ် Password မှားနေပါတယ်။"
        return render_template_string(LOGIN_HTML, error=error_msg)
        
    return render_template_string(LOGIN_HTML, error=None)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


# ---------------------------------------------------------
# 🌐 Main Routes
# ---------------------------------------------------------
@app.route('/')
def index():
    return render_template('index.html')

# 👇 စပါး Guide လမ်းကြောင်းများ 👇
@app.route('/guide/rice')
def rice_guide():
    return render_template('rice.html')

@app.route('/guide/monsoon_rice')
def monsoon_rice_guide():
    return render_template('monsoon_rice.html')

@app.route('/guide/summer_rice')
def summer_rice_guide():
    return render_template('summer_rice.html')
# 👆 ------------------------------------------------- 👆

@app.route('/guide/tea')
def tea_guide():
    return render_template('tea.html')

@app.route('/guide/corn')
def corn_guide():
    return render_template('corn.html')

@app.route('/guide/rubber')
def rubber_guide():
    return render_template('rubber.html')

@app.route('/guide/coffee')
def coffee_guide():
    return render_template('coffee.html')

@app.route('/guide/peanut')
def peanut_guide():
    return render_template('nut.html')

@app.route('/guide/strawberry')
def strawberry_guide():
    return render_template('strawberry.html')

@app.route('/guide/crab_apple')
def crab_apple_guide():
    return render_template('crab_apple.html')

@app.route('/guide/damson')
def damson_guide():
    return render_template('damson.html')

@app.route('/guide/watermelon')
def watermelon_guide():
    return render_template('watermelon.html')

@app.route('/guide/pineapple')
def pineapple_guide():
    return render_template('pineapple.html')

@app.route('/api/farms')
def get_farms():
    df = pd.read_sql("SELECT * FROM farms", engine)
    df = df.where(pd.notnull(df), None)
    return jsonify(df.to_dict(orient='records'))

@app.route('/api/guide/<crop_name>')
def get_guide(crop_name):
    search_term = crop_name.replace('_', ' ').strip()
    query = f"SELECT * FROM crop_guides WHERE crop_name ILIKE '%%{search_term}%%' LIMIT 1"
    df = pd.read_sql(query, engine)
    
    if not df.empty:
        return jsonify(df.iloc[0].to_dict())
        
    return jsonify({"error": "Guide not found"})

@app.route('/api/weather/<farm_id>')
def get_weather(farm_id):
    farm_df = pd.read_sql(f"SELECT * FROM farms WHERE farm_id = '{farm_id}'", engine)
    if farm_df.empty:
        return jsonify({"error": "Farm not found"})
    
    farm = farm_df.iloc[0]
    f_lat, f_lon = farm['latitude'], farm['longitude']

    stations_df = pd.read_sql("SELECT * FROM weather_stations", engine)
    min_dist = float('inf')
    nearest_station = None
    
    for _, st in stations_df.iterrows():
        R = 6371 
        dLat = math.radians(st['latitude'] - f_lat)
        dLon = math.radians(st['longitude'] - f_lon)
        a = math.sin(dLat/2) * math.sin(dLat/2) + math.cos(math.radians(f_lat)) * math.cos(math.radians(st['latitude'])) * math.sin(dLon/2) * math.sin(dLon/2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        dist = R * c
        
        if dist < min_dist:
            min_dist = dist
            nearest_station = st['station_name']

    weather_query = """
        SELECT date::text, "T2M" as temp, "PRECTOTCORR" as rainfall 
        FROM weather_data 
        ORDER BY date DESC LIMIT 7
    """
    weather_df = pd.read_sql(weather_query, engine)
    
    # ✅ ရက်စွဲဖော်မတ် မှန်ကန်တာကိုပဲ ယူမယ်
    weather_df = weather_df[weather_df['date'].astype(str).str.match(r'^(\d{8}|\d{4}-\d{2}-\d{2})$', na=False)]
    weather_df = weather_df.sort_values('date').reset_index(drop=True)

    return jsonify({
        "nearest_station": nearest_station,
        "distance_km": round(min_dist, 2),
        "weather_data": weather_df.to_dict(orient='records')
    })


# =======================================================
# 📈 သီးနှံစျေးနှုန်း API
# =======================================================
@app.route('/api/crop_price/<crop_name>')
def get_crop_price(crop_name):
    try:
        with engine.connect() as conn:
            search_name = crop_name.split('(')[0].strip()
            query = text("SELECT * FROM crop_prices WHERE crop_name ILIKE :name")
            result = conn.execute(query, {"name": f"%{search_name}%"}).fetchone()
            
            if result:
                row = dict(result._mapping)
                price_text = f"{row['min_price']:,} - {row['max_price']:,} ကျပ်"
                return jsonify({
                    "success": True,
                    "crop_name": row['crop_name_mm'],
                    "price": price_text,
                    "unit": row['unit'],
                    "note": row['note']
                })
            else:
                return jsonify({"success": False, "error": "ဤသီးနှံအတွက် စျေးနှုန်း မရှိပါ"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/all_crop_prices')
def get_all_crop_prices():
    try:
        df = pd.read_sql("SELECT * FROM crop_prices", engine)
        
        result_data = []
        for _, row in df.iterrows():
            item = row.to_dict()
            crop_name = item.get('crop_name')
            
            try:
                hist = pd.read_sql(text("""
                    SELECT min_price FROM price_history 
                    WHERE crop_name = :c 
                    ORDER BY recorded_date DESC, updated_at DESC 
                    LIMIT 2
                """), engine, params={"c": crop_name})
                
                if len(hist) >= 2:
                    latest = hist.iloc[0]['min_price']
                    prev = hist.iloc[1]['min_price']
                    item['change'] = int(latest - prev)
                else:
                    item['change'] = None
            except Exception:
                item['change'] = None
            
            result_data.append(item)
        
        return jsonify({"success": True, "data": result_data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# =======================================================
# 📈 သီးနှံဈေးနှုန်း သမိုင်းကြောင်းနှင့် ခန့်မှန်းချက် API
# =======================================================
@app.route('/api/price_history/<crop_name>')
def get_price_history_trend(crop_name):
    days = request.args.get('days', 7, type=int)
    try:
        query = text("""
            SELECT 
                recorded_date::text AS recorded_date,
                min_price,
                max_price,
                updated_at
            FROM price_history 
            WHERE crop_name = :c 
            ORDER BY recorded_date DESC, updated_at DESC
            LIMIT :d
        """)
        df = pd.read_sql(query, engine, params={"c": crop_name, "d": days})

        if df.empty:
            return jsonify({
                "success": False,
                "message": "ဒီသီးနှံအတွက် ဈေးနှုန်းမှတ်တမ်း မရှိပါ",
                "data": [],
                "history": [],
                "forecast": []
            })

        df = df.sort_values(by=['recorded_date', 'updated_at']).reset_index(drop=True)
        df['updated_at'] = df['updated_at'].astype(str)

        daily_diff = 0
        trend = "same"
        if len(df) >= 2:
            latest_min = int(df.iloc[-1]['min_price'])
            prev_min = int(df.iloc[-2]['min_price'])
            daily_diff = latest_min - prev_min
            trend = "up" if daily_diff > 0 else ("down" if daily_diff < 0 else "same")

        forecast = []
        if len(df) >= 1:
            window_size = min(3, len(df))
            last_n_min = df['min_price'].tail(window_size).mean()
            last_n_max = df['max_price'].tail(window_size).mean()
            
            try:
                last_date_str = df.iloc[-1]['recorded_date']
                last_date = datetime.strptime(str(last_date_str), "%Y-%m-%d")
            except Exception:
                last_date = datetime.now()
            
            for i in range(1, 4):
                forecast_date = (last_date + timedelta(days=i)).strftime("%Y-%m-%d")
                forecast.append({
                    "date": forecast_date,
                    "min_price": int(round(last_n_min)),
                    "max_price": int(round(last_n_max))
                })

        data_list = df[['recorded_date', 'min_price', 'max_price', 'updated_at']].to_dict(orient='records')

        return jsonify({
            "success": True,
            "data": data_list,
            "history": data_list, 
            "daily_diff": int(daily_diff),
            "trend": trend,
            "forecast": forecast
        })
    except Exception as e:
        print(f"❌ Price History Error: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "data": [],
            "history": [],
            "forecast": []
        })


@app.route('/api/predict', methods=['POST'])
def predict():
    if model is None:
        return jsonify({'error': 'Model not loaded'}), 500
    
    data = request.json
    try:
        features = pd.DataFrame([[
            data['N'], data['P'], data['K'], 
            data['temperature'], data['humidity'], data['ph'], data['rainfall']
        ]], columns=['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall'])
        
        prediction = model.predict(features)[0]

        top3 = []
        if hasattr(model, 'predict_proba'):
            proba = model.predict_proba(features)[0]
            top3_idx = proba.argsort()[::-1][:3]
            top3 = [{"crop": str(model.classes_[i]), "probability": round(float(proba[i]) * 100, 1)}
                    for i in top3_idx]

        importances = model.feature_importances_
        features_names = features.columns
        importance_dict = dict(zip(features_names, importances))
        top_features = dict(sorted(importance_dict.items(), key=lambda item: item[1], reverse=True)[:3])

        return jsonify({
            'prediction': prediction,
            'top3': top3,
            'top_features': top_features
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# =========================================================
# 🌧️ မိုးရေ Alert System (Historical + Real Forecast)
# =========================================================
FORECAST_API_KEY = '4f4a58051cf6cbea0fe0e181024354bc'

HEAVY_RAIN_MM = 50
HIGH_RAIN_MM = 30
CUM3_FLOOD_MM = 100
AVG7_WET_MM = 15
AVG7_DRY_MM = 1
HEAT_TEMP_C = 35
FORECAST_LOOKAHEAD_DAYS = 3


def add_alert(alerts, date, severity, icon, title_mm, msg_mm, title_en, msg_en, value=None):
    alerts.append({
        "date": date,
        "severity": severity,
        "icon": icon,
        "title_mm": title_mm,
        "message_mm": msg_mm,
        "title_en": title_en,
        "message_en": msg_en,
        "value": round(value, 1) if value is not None else None
    })


def nice_date(d):
    d = str(d).strip()
    # ရက်စွဲဖော်မတ် မှန်မမှန် တိုက်ရိုက်စစ်မယ် (ဥပမာ - 2026-11-06)
    match = re.match(r'^(\d{4})-(\d{2})-(\d{2})$', d)
    if match:
        yyyy, mm, dd = match.groups()
        return f"{int(dd)}-{int(mm)}-{yyyy}"  # 6-11-2026 ပုံစံ ထွက်လာမယ်
    
    # 20261106 ပုံစံအတွက်
    match2 = re.match(r'^(\d{4})(\d{2})(\d{2})$', d)
    if match2:
        yyyy, mm, dd = match2.groups()
        return f"{int(dd)}-{int(mm)}-{yyyy}"
        
    return d


def analyze_daily_rain(alerts, date_str, rain_mm, prefix_mm="", prefix_en=""):
    if rain_mm >= HEAVY_RAIN_MM:
        add_alert(alerts, date_str, "red", "🌧️",
            f"{prefix_mm}ပြင်းထန်သော မိုးရေချိန်",
            f"{nice_date(date_str)} တွင် မိုးရေ {rain_mm:.0f} mm ရှိပါမည်။ ရေကြီးရေလျှံမှုများဖြစ်နိုင်ပါတယ် — မြောင်းစွန့်များ ပိတ်ဆို့မနေစေရန် စစ်ဆေးရပါမည်",
            f"{prefix_en}Heavy Rainfall",
            f"{rain_mm:.0f} mm rainfall expected on {nice_date(date_str)}.",
            rain_mm)
    elif rain_mm >= HIGH_RAIN_MM:
        add_alert(alerts, date_str, "yellow", "🌦️",
            f"{prefix_mm}မိုးရွာသွန်းမှုများနိုင်ပါသည်",
            f"{nice_date(date_str)} တွင် မိုးရေ {rain_mm:.0f} mm ရှိပါမည်။ မြေသြဇာနှင့် မြေဆီလွှာများ ပျက်စီးဆုံးရှုံးမှု ဖြစ်နိုင်ပါသည်။",
            f"{prefix_en}High Rainfall",
            f"{rain_mm:.0f} mm rainfall on {nice_date(date_str)}.",
            rain_mm)


def fetch_forecast(lat, lon):
    if not FORECAST_API_KEY or FORECAST_API_KEY.startswith('သင့်'):
        return []
    try:
        resp = requests.get(
            "https://api.openweathermap.org/data/2.5/forecast",
            params={"lat": lat, "lon": lon, "appid": FORECAST_API_KEY, "units": "metric"},
            timeout=5
        )
        data = resp.json()
        daily = {}
        for item in data.get("list", []):
            day = item["dt_txt"][:10]
            rain = item.get("rain", {}).get("3h", 0)
            temp = item["main"]["temp"]
            if day not in daily:
                daily[day] = {"rain": 0, "temp_max": temp}
            daily[day]["rain"] += rain
            daily[day]["temp_max"] = max(daily[day]["temp_max"], temp)
        return sorted([(day, v["rain"], v["temp_max"]) for day, v in daily.items()])
    except Exception:
        return []


@app.route('/api/alerts/<farm_id>')
def get_alerts(farm_id):
    farm_df = pd.read_sql(f"SELECT * FROM farms WHERE farm_id = '{farm_id}'", engine)
    if farm_df.empty:
        return jsonify({"alerts": [], "level": "green", "forecast_available": False})

    farm = farm_df.iloc[0]
    alerts = []

    weather_df = pd.read_sql("""
        SELECT date::text, "T2M" as temp, "PRECTOTCORR" as rainfall
        FROM weather_data
        ORDER BY date DESC LIMIT 14
    """, engine)

    if not weather_df.empty:
        # ✅ ရက်စွဲဖော်မတ် YYYY-MM-DD မှန်တာကိုသာ ယူမယ် (junk ရက်စွဲတွေ မှားယွင်းစဉ်းဝင်ရန် မပေးဘူး)
                # ✅ ရက်စွဲဖော်မတ်က YYYY-MM-DD (သို့မဟုတ်) YYYYMMDD ဖြစ်မှ လက်ခံမယ်
        weather_df = weather_df[weather_df['date'].str.match(r'^(\d{4}-\d{2}-\d{2}|\d{8})$', na=False)]
        weather_df = weather_df.reset_index(drop=True)

        # ✅ အပူချိန်နဲ့ မိုးရေချိန် အနုတ်ကိန်းတွေကို ဖယ်မယ်
        weather_df = weather_df[(weather_df['temp'] > -50) & (weather_df['rainfall'] >= 0)]
        
        # ✅ Pandas ကို သုံးပြီး ရက်စွဲဖော်မတ် မမှန်တာတွေကို NaT (Not a Time) အဖြစ်ပြောင်းပြီး ဖျက်မယ်
        weather_df['date'] = pd.to_datetime(weather_df['date'], errors='coerce', format='%Y-%m-%d')
        weather_df = weather_df.dropna(subset=['date']) # NaT တွေကို ဖယ်မယ်
        
        # ပြန်ပြီး ရက်စွဲအလိုက် စီမယ်
        weather_df = weather_df.sort_values('date').reset_index(drop=True)

        # ✅ ရက်စွဲကို ပြန်ပြီး စာသား (String) အဖြစ် ပြောင်းမယ် (YYYY-MM-DD ပုံစံ)
        weather_df['date'] = weather_df['date'].dt.strftime('%Y-%m-%d')

        # ✅ Data ရှိမှ ဆက်လုပ်မယ်
        if not weather_df.empty:
            for _, row in weather_df.iterrows():
                analyze_daily_rain(alerts, row['date'], float(row['rainfall']))

            for i in range(2, len(weather_df)):
                cum3 = weather_df.loc[i-2:i, 'rainfall'].sum()
                if cum3 >= CUM3_FLOOD_MM:
                    end_d = weather_df.loc[i, 'date']
                    add_alert(alerts, end_d, "red", "⚠️",
                        "မိုးများ အဆက်မပြတ်ရွာသွန်းပါက — ရေကြီးမှုအန္တရာယ်ဖြစ်နိုင်",
                        f"နောက်ဆုံး ၃ ရက်အတွင်း မိုးရေ {cum3:.0f} mm ရှိပါပြီ။ ရေကြီးရေလျှံမှုများ ရှိနိုင်ပါသည်။",
                        "Continuous Rainfall",
                        f"{cum3:.0f} mm accumulated over 3 days.", cum3)
                    break

            last7 = weather_df.tail(7)
            avg7 = last7['rainfall'].mean()
            latest_d = weather_df.iloc[-1]['date']

            if avg7 >= AVG7_WET_MM:
                add_alert(alerts, latest_d, "orange", "🌊",
                    "ရေကြီးရေလျှံစတင်ဖြစ်ပေါ်နိုင်ခြင်း သတိပေးချက်",
                    f"နောက်ဆုံး ၇ ရက်ပျမ်းမျှ မိုးရေချိန် {avg7:.1f} mm/ရက် ဖြစ်နေပါပြီ။",
                    "Flooding Trend Warning", f"7-day average is {avg7:.1f} mm/day.", avg7)
            elif avg7 <= AVG7_DRY_MM:
                add_alert(alerts, latest_d, "orange", "☀️",
                    "ရေစခမ်းခြောက်ခြင်း သတိပေးချက်",
                    f"မိုးရေချိန်မှတ် အလွန်နည်းနေပါပြီ (ပျမ်းမျှ {avg7:.1f} mm/ရက်)။ ရေလောင်းပေးရန် တိုက်တွန်းလိုပါသည်။",
                    "Drought Warning", f"Very low rainfall ({avg7:.1f} mm/day).", avg7)

    forecast = fetch_forecast(farm['latitude'], farm['longitude'])
    for day_str, rain_mm, temp_max in forecast[:FORECAST_LOOKAHEAD_DAYS]:
        date_key = day_str.replace("-", "")
        fc_list = []
        analyze_daily_rain(fc_list, date_key, rain_mm, prefix_mm="ခန့်မှန်း — ", prefix_en="Forecast: ")
        for a in fc_list:
            a["message_mm"] += " (ခန့်မှန်းချက်ဖြစ်ပါသည်)"
        alerts.extend(fc_list)

        if temp_max >= HEAT_TEMP_C:
            add_alert(alerts, date_key, "orange", "🔥",
                "ခန့်မှန်း — အပူလှိုင်း",
                f"{nice_date(date_key)} တွင် အပူချိန် {temp_max:.0f}°C အထိ ရှိနိုင်ပါသည်။ နေ့လယ် ၁၂-၃ နာရီအတွင်း နေပူပြင်းနိုင်သည့်အတွက် သတိပြုရန်",
                "Forecast: Heat Wave",
                f"{temp_max:.0f}°C expected on {nice_date(date_key)}.", temp_max)

    level = "green"
    if any(a["severity"] == "red" for a in alerts):
        level = "red"
    elif any(a["severity"] == "orange" for a in alerts):
        level = "orange"
    elif any(a["severity"] == "yellow" for a in alerts):
        level = "yellow"

    sev_order = {"red": 0, "orange": 1, "yellow": 2}
    alerts.sort(key=lambda a: (sev_order[a["severity"]], a["date"]))

    if level == "red":
        try:
            notify_subscribers(farm_id, farm['farm_name'], alerts[:3])
        except Exception as e:
            print(f"⚠️ Email notification error: {e}")

    return jsonify({
        "farm_name": farm['farm_name'],
        "level": level,
        "alert_count": len(alerts),
        "forecast_available": len(forecast) > 0,
        "alerts": alerts[:8]
    })


# =========================================================
# 📧 Email Notification
# =========================================================
def send_email(to_email, subject, body):
    msg = MIMEMultipart()
    msg['From'] = SMTP_EMAIL
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.send_message(msg)


def notify_subscribers(farm_id, farm_name, alerts):
    today = datetime.now().strftime("%Y-%m-%d")
    subs = pd.read_sql(
        f"SELECT * FROM alert_subscriptions WHERE farm_id = '{farm_id}' OR farm_id = 'ALL'", engine)

    for _, sub in subs.iterrows():
        if sub['last_sent_date'] == today:
            continue

        body_lines = [f"🌾 AgroSmart Kengtung Alert System\n", f"🏡 စိုက်ခင်း: {farm_name}\n"]
        for a in alerts:
            body_lines.append(f"\n🚨 {a['title_mm']}\n{a['message_mm']}\nရက်စွဲ: {nice_date(a['date'])}")
        body_lines.append("\n\n— AgroSmart Kengtung")
        send_email(sub['email'], f"🚨 အန္တရာယ် Alert — {farm_name}", "".join(body_lines))

        with engine.begin() as conn:
            conn.execute(text("UPDATE alert_subscriptions SET last_sent_date = :d WHERE id = :i"),
                         {"d": today, "i": int(sub['id'])})


@app.route('/api/subscribe', methods=['POST'])
def subscribe():
    data = request.json
    email = data.get('email', '').strip()
    farm_id = data.get('farm_id', '').strip()

    if not email or '@' not in email:
        return jsonify({'success': False, 'message': '❌ Email မှားယွင်းနေပါသည်'}), 400

    try:
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO alert_subscriptions (email, farm_id, last_sent_date)
                VALUES (:e, :f, '')
                ON CONFLICT (email, farm_id) DO NOTHING
            """), {"e": email, "f": farm_id})
        return jsonify({'success': True,
                        'message': f'✅ {email} ကို ဒီ {farm_id} အတွက် alert ပို့ပါလိမ့်မယ်'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'❌ Error: {e}'}), 500


# =========================================================
# 🗓️ Crop Calendar
# =========================================================
MONTH_MAP = {'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5,
             'june': 6, 'july': 7, 'august': 8, 'september': 9, 'october': 10,
             'november': 11, 'december': 12}
MONTHS_MM = {1: 'ဇန်နဝါရီ', 2: 'ဖေဖော်ဝါရီ', 3: 'မတ်', 4: 'ဧပြီ', 5: 'မေ', 6: 'ဇွန်',
             7: 'ဇူလိုင်', 8: 'ဩဂုတ်', 9: 'စက်တင်ဘာ', 10: 'အောက်တိုဘာ',
             11: 'နိုဝင်ဘာ', 12: 'ဒီဇင်ဘာ'}

CROP_MM_MAP = {
    'Rice': 'စပါး',
    'Tea': 'လက်ဖက်',
    'Watermelon': 'ဖရဲ',
    'Strawberry': 'စတော်ဘယ်ရီ',
    'Corn': 'ပြောင်း',
    'Peanut': 'မြေပဲ',
    'Rubber': 'ရော်ဘာ',
    'Crab Apple': 'ကြက်မောက်'
}

def months_from_string(s):
    s_en = re.sub(r'\(.*?\)', '', str(s)).lower().strip()
    months = set()
    m = re.search(r'([a-z]+)\s*-\s*([a-z]+)', s_en)
    if m and m.group(1) in MONTH_MAP and m.group(2) in MONTH_MAP:
        a, b = MONTH_MAP[m.group(1)], MONTH_MAP[m.group(2)]
        if a <= b:
            months.update(range(a, b + 1))
        else:
            months.update(range(a, 13))
            months.update(range(1, b + 1))
    for name, n in MONTH_MAP.items():
        if name in s_en:
            months.add(n)
    return months


@app.route('/api/calendar')
def crop_calendar():
    now_month = datetime.now().month
    farms_df = pd.read_sql(
        "SELECT farm_name, current_crop, planting_month, harvest_month FROM farms", engine)

    planting, harvesting = [], []
    for _, f in farms_df.iterrows():
        crop_en = str(f['current_crop']).split('(')[0].strip()
        crop_mm = CROP_MM_MAP.get(crop_en, crop_en)

        if now_month in months_from_string(f['planting_month']):
            planting.append({"crop": crop_mm, "farm": f['farm_name']})
        if now_month in months_from_string(f['harvest_month']):
            harvesting.append({"crop": crop_mm, "farm": f['farm_name']})

    return jsonify({
        "month": now_month,
        "month_mm": MONTHS_MM[now_month],
        "year": datetime.now().year,
        "planting": planting,
        "harvesting": harvesting
    })

@app.route('/weather')
def weather_page():
    return render_template('weather.html')

@app.route('/api/weather/full/<farm_id>')
def get_full_weather(farm_id):
    farm_df = pd.read_sql(f"SELECT * FROM farms WHERE farm_id = '{farm_id}'", engine)
    if farm_df.empty:
        return jsonify({"error": "Farm not found"})
    
    farm = farm_df.iloc[0]
    f_lat, f_lon = farm['latitude'], farm['longitude']

    stations_df = pd.read_sql("SELECT * FROM weather_stations", engine)
    min_dist = float('inf')
    nearest_station = None
    
    for _, st in stations_df.iterrows():
        R = 6371 
        dLat = math.radians(st['latitude'] - f_lat)
        dLon = math.radians(st['longitude'] - f_lon)
        a = math.sin(dLat/2) * math.sin(dLat/2) + math.cos(math.radians(f_lat)) * math.cos(math.radians(st['latitude'])) * math.sin(dLon/2) * math.sin(dLon/2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        dist = R * c
        if dist < min_dist:
            min_dist = dist
            nearest_station = st['station_name']

    latest_date_query = "SELECT MAX(date) as max_date FROM weather_data"
    latest_date_df = pd.read_sql(latest_date_query, engine)
    
    if latest_date_df.empty or pd.isna(latest_date_df['max_date'].iloc[0]):
        return jsonify({"error": "No weather data available"})
        
    max_date = latest_date_df['max_date'].iloc[0]

    weather_query = f"""
        SELECT date::text, "T2M" as temp, "PRECTOTCORR" as rainfall
        FROM weather_data 
        WHERE date <= '{max_date}' 
        ORDER BY date DESC 
        LIMIT 7
    """
    weather_df = pd.read_sql(weather_query, engine)
    
    # ✅ ရက်စွဲဖော်မတ် YYYY-MM-DD မှန်တာကိုသာ ယူမယ်
    weather_df = weather_df[weather_df['date'].astype(str).str.match(r'^\d{4}-\d{2}-\d{2}$', na=False)]
    weather_df['date'] = pd.to_datetime(weather_df['date'], errors='coerce', format='%Y-%m-%d')
    weather_df = weather_df.dropna(subset=['date'])
    weather_df = weather_df.sort_values('date')

    weather_df = weather_df[(weather_df['temp'] > -50) & (weather_df['rainfall'] >= 0)]

    if weather_df.empty:
        return jsonify({"error": "No valid weather data available"})

    latest_weather = weather_df.iloc[-1].to_dict()
    latest_weather['humidity'] = round(60 + (latest_weather['rainfall'] * 0.5), 1)
    latest_weather['wind'] = round(2.0 + (latest_weather['temp'] * 0.05), 1)
    latest_weather['date'] = latest_weather['date'].strftime('%Y-%m-%d')

    weather_data_list = []
    for _, r in weather_df.iterrows():
        weather_data_list.append({
            "date": r['date'].strftime('%Y-%m-%d'),
            "temp": r['temp'],
            "rainfall": r['rainfall']
        })

    return jsonify({
        "nearest_station": nearest_station,
        "distance_km": round(min_dist, 2),
        "latest_weather": latest_weather,
        "weather_data": weather_data_list
    })
    
@app.route('/api/weather/city/kengtung')
def get_city_weather():
    city_lat, city_lon = 21.29, 99.60

    stations_df = pd.read_sql("SELECT * FROM weather_stations", engine)
    min_dist = float('inf')
    nearest_station = None
    
    for _, st in stations_df.iterrows():
        R = 6371 
        dLat = math.radians(st['latitude'] - city_lat)
        dLon = math.radians(st['longitude'] - city_lon)
        a = math.sin(dLat/2) * math.sin(dLat/2) + math.cos(math.radians(city_lat)) * math.cos(math.radians(st['latitude'])) * math.sin(dLon/2) * math.sin(dLon/2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        dist = R * c
        
        if dist < min_dist:
            min_dist = dist
            nearest_station = st['station_name']

    latest_date_query = "SELECT MAX(date) as max_date FROM weather_data"
    latest_date_df = pd.read_sql(latest_date_query, engine)
    
    if latest_date_df.empty or pd.isna(latest_date_df['max_date'].iloc[0]):
        return jsonify({"error": "No weather data available"})
        
    max_date = latest_date_df['max_date'].iloc[0]

    weather_query = f"""
        SELECT date::text, "T2M" as temp, "PRECTOTCORR" as rainfall
        FROM weather_data 
        WHERE date <= '{max_date}' 
        ORDER BY date DESC LIMIT 7
    """
    weather_df = pd.read_sql(weather_query, engine)
    
    # ✅ ရက်စွဲဖော်မတ် YYYY-MM-DD မှန်တာကိုသာ ယူမယ်
    weather_df = weather_df[weather_df['date'].astype(str).str.match(r'^\d{4}-\d{2}-\d{2}$', na=False)]
    weather_df['date'] = pd.to_datetime(weather_df['date'], errors='coerce', format='%Y-%m-%d')
    weather_df = weather_df.dropna(subset=['date'])
    weather_df = weather_df.sort_values('date')

    weather_df = weather_df[(weather_df['temp'] > -50) & (weather_df['rainfall'] >= 0)]

    if weather_df.empty:
        return jsonify({"error": "No valid data"})

    latest = weather_df.iloc[-1].to_dict()

    weather_data_list = []
    for _, r in weather_df.iterrows():
        weather_data_list.append({
            "date": r['date'].strftime('%Y-%m-%d'),
            "temp": r['temp'],
            "rainfall": r['rainfall']
        })

    return jsonify({
        "city_name": "ကျိုင်းတုံမြို့",
        "nearest_station": nearest_station,
        "current_temp": latest['temp'],
        "current_rain": latest['rainfall'],
        "weather_data": weather_data_list
    })

@app.route('/api/forecast/city')
def get_city_forecast():
    lat, lon = 21.29, 99.60

    try:
        resp = requests.get(
            "https://api.openweathermap.org/data/2.5/forecast",
            params={"lat": lat, "lon": lon, "appid": FORECAST_API_KEY, "units": "metric"},
            timeout=5
        )
        data = resp.json()
        
        daily_data = {}
        for item in data.get("list", []):
            date_str = item["dt_txt"][:10] 
            
            if date_str not in daily_data:
                daily_data[date_str] = {
                    "date": date_str,
                    "temp_min": item["main"]["temp_min"],
                    "temp_max": item["main"]["temp_max"],
                    "humidity": item["main"]["humidity"],
                    "wind": item["wind"]["speed"],
                    "weather_condition": item["weather"][0]["main"],
                    "description": item["weather"][0]["description"],
                    "icon": item["weather"][0]["icon"],
                    "rain": 0
                }
            else:
                daily_data[date_str]["temp_min"] = min(daily_data[date_str]["temp_min"], item["main"]["temp_min"])
                daily_data[date_str]["temp_max"] = max(daily_data[date_str]["temp_max"], item["main"]["temp_max"])
                
            if "rain" in item:
                daily_data[date_str]["rain"] += item["rain"].get("3h", 0)

        sorted_dates = sorted(daily_data.keys())
        result = []
        for d in sorted_dates[:3]:
            day_info = daily_data[d]
            cond_map = {"Clear": "နေသာ", "Clouds": "တိမ်ထူ", "Rain": "မိုးရွာ", "Drizzle": "မိုးဖွဲ"}
            day_info["condition_mm"] = cond_map.get(day_info["weather_condition"], "အခြေအနေမသိ")
            result.append(day_info)

        return jsonify({"forecast": result})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =========================================================
# 🤖 Cosine Similarity Chatbot (Database Base)
# =========================================================
try:
    df_dataset = pd.read_sql("SELECT question, answer FROM crop_dataset", engine)
    
    if not df_dataset.empty:
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(df_dataset['question'])
        print("✅ Cosine Similarity Dataset loaded from Database!")
    else:
        print("⚠️ Database ထဲမှာ Data မရှိသေးပါ။")
        df_dataset = None
except Exception as e:
    print(f"⚠️ Dataset loading error: {e}")
    df_dataset = None

@app.route('/chatbot_similarity')
def chatbot_similarity_page():
    return render_template('chat_similarity.html')

@app.route('/api/chat_similarity', methods=['POST'])
def chat_similarity():
    if df_dataset is None or df_dataset.empty:
        return jsonify({'error': 'Dataset not loaded properly.'}), 500

    data = request.json
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({'error': 'Message is empty'}), 400

    try:
        user_vec = vectorizer.transform([user_message])
        similarities = cosine_similarity(user_vec, tfidf_matrix).flatten()
        best_match_idx = similarities.argmax()
        best_score = similarities[best_match_idx]
        
        # 👇 ဒီနေရာမှာ ပြင်ထားပါတယ် (မသိရင် Database ထဲ သိမ်းမယ်)
        if best_score < 0.2: # 0.2 ထက်နည်းရင် မသိဘူးလို့ သတ်မှတ်မယ်
            best_answer = "တောင်းပန်ပါတယ်။ အဲ့ဒီမေးခွန်းအတွက် အဖြေကို ကျွန်တော် မသိသေးပါဘူး။ Admin မှ ထည့်သွင်းပေးသွားပါမယ်။"
            
            # မေးခွန်းအသစ်ကို သီးသန့် Table ထဲ သိမ်းမယ်
            with engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO unanswered_questions (user_id, question) 
                    VALUES (:uid, :q)
                """), {"uid": session.get('user_id'), "q": user_message})
                
        else:
            best_answer = df_dataset.iloc[best_match_idx]['answer']
            
        if 'user_id' in session:
            with engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO chat_history (user_id, user_message, bot_response) 
                    VALUES (:uid, :umsg, :breply)
                """), {"uid": session['user_id'], "umsg": user_message, "breply": best_answer})
            
        return jsonify({'reply': best_answer})
    except Exception as e:
        print(f"Similarity Chatbot Error: {e}")
        return jsonify({'error': str(e)}), 500


# 👇 Admin Panel အတွက် Unanswered Questions တွေကို ဆွဲထုတ်မယ့် API အသစ်
@app.route('/api/admin/unanswered_questions')
def get_unanswered_questions():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        df = pd.read_sql("""
            SELECT q.id, u.username, q.question, q.created_at 
            FROM unanswered_questions q
            LEFT JOIN users u ON q.user_id = u.id
            ORDER BY q.created_at DESC LIMIT 50
        """, engine)
        df['created_at'] = df['created_at'].astype(str)
        return jsonify({"success": True, "data": df.to_dict(orient='records')})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    
@app.route('/api/get_chat_history', methods=['GET'])
def get_chat_history():
    if 'user_id' not in session:
        return jsonify({'history': []})
        
    df_history = pd.read_sql(f"SELECT user_message, bot_response FROM chat_history WHERE user_id = {session['user_id']} ORDER BY created_at ASC", engine)
    return jsonify({'history': df_history.to_dict(orient='records')})


@app.route('/api/admin/delete_unanswered', methods=['POST'])
def delete_unanswered():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    question = data.get('question')
    
    try:
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM unanswered_questions WHERE question = :q"), {"q": question})
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# =========================================================
# 🌱 Crop Parameter Guide (သီးနှံအလိုက် လမ်းညွှန်)
# =========================================================
@app.route('/crop_guide_params')
def crop_guide_params():
    try:
        df = pd.read_sql("SELECT * FROM crop_params", engine)
        guide_data = {}
        for _, row in df.iterrows():
            crop_name = row.get('Crop') or row.get('crop_name') or row.get('crop')
            if not crop_name or pd.isna(crop_name):
                continue
            guide_data[crop_name] = {
                "desc": f"{crop_name} စိုက်ပျိုးရန် သင့်တော်သော အခြေအနေများ",
                "N": f"{row.get('N_min', '-')} မှ {row.get('N_max', '-')} (kg/ha) ကြား လိုအပ်သည်။",
                "P": f"{row.get('P_min', '-')} မှ {row.get('P_max', '-')} (kg/ha) ကြား လိုအပ်သည်။",
                "K": f"{row.get('K_min', '-')} မှ {row.get('K_max', '-')} (kg/ha) ကြား လိုအပ်သည်။",
                "temp": f"{row.get('Temp_min', '-')}°C မှ {row.get('Temp_max', '-')}°C ကြား အကောင်းဆုံးဖြစ်သည်။",
                "humidity": f"{row.get('Humidity_min', '-')}% မှ {row.get('Humidity_max', '-')}% ကြား လိုအပ်သည်။",
                "ph": f"{row.get('pH_min', '-')} မှ {row.get('pH_max', '-')} ကြား ဖြစ်သင့်သည်။",
                "rainfall": f"{row.get('Rainfall_min', '-')} မှ {row.get('Rainfall_max', '-')} mm ကြား လိုအပ်သည်။"
            }

        soil_df = pd.read_sql("SELECT soil_type, recommended_crops FROM soil_crop_mapping", engine)
        
        crop_soil_map = {}
        for _, row in soil_df.iterrows():
            soil_name = row['soil_type']
            crops = [c.strip() for c in row['recommended_crops'].split(',')]
            for crop in crops:
                if crop not in crop_soil_map:
                    crop_soil_map[crop] = []
                soil_mm_map = {
                    "Meadow & Meadow Alluvial Soils": "မြက်ခင်းမြေ",
                    "Gley & Gley Swampy Soils": "ရွံ့ပြာမြေ",
                    "Red Brown Forest Soils": "နီညိုရောင်သစ်တောမြေ",
                    "Yellow Brown Forest Soils": "ဝါညိုရောင်သစ်တောမြေ",
                    "Red Earths & Yellow Earths": "အနီ/အဝါရောင်မြေ",
                    "Mountainous Brown Forest Soils": "တောင်ပေါ်ညိုရောင်မြေ",
                    "Mountainous Red Forest Soils": "တောင်ပေါ်အနီရောင်မြေ",
                    "Alluvial": "အနည်ထိုင်မြေ",
                    "Lateritic": "နီညိုရောင်မြေ"
                }
                mm_name = soil_mm_map.get(soil_name, soil_name)
                if mm_name not in crop_soil_map[crop]:
                    crop_soil_map[crop].append(mm_name)

        for crop_name in guide_data:
            for key in crop_soil_map:
                if key in crop_name:
                    guide_data[crop_name]['soils'] = crop_soil_map[key]
                    break
            else:
                guide_data[crop_name]['soils'] = []

    except Exception as e:
        print(f"⚠️ Crop Parameter Error: {e}")
        guide_data = {}
    
    return render_template('crop_guide_params.html', guide_data=guide_data)

# =========================================================
# 👑 Admin Panel Routes
# =========================================================
@app.route('/admin')
def admin_dashboard():
    if session.get('role') != 'admin':
        return "⛔ Admin သာ ဝင်ခွင့်ရှိသည်။"
    
    df_users = pd.read_sql("SELECT id, username, role FROM users", engine)
    users = df_users.to_dict(orient='records')
    
    df_history = pd.read_sql("""
        SELECT h.id, u.username, h.user_message, h.bot_response, h.created_at 
        FROM chat_history h 
        JOIN users u ON h.user_id = u.id 
        ORDER BY h.created_at DESC LIMIT 20
    """, engine)
    history = df_history.to_dict(orient='records')
    
    df_dataset = pd.read_sql("SELECT id, question, answer FROM crop_dataset ORDER BY id DESC LIMIT 50", engine)
    datasets = df_dataset.to_dict(orient='records')
    
    df_farms = pd.read_sql("SELECT * FROM farms LIMIT 10", engine)
    farms = df_farms.to_dict(orient='records')

    df_news = pd.read_sql("SELECT * FROM agri_news ORDER BY created_at DESC", engine)
    df_news['created_at'] = df_news['created_at'].astype(str)
    news_list = df_news.to_dict(orient='records')
    
    return render_template('admin.html', users=users, history=history, datasets=datasets, farms=farms, news_list=news_list)

@app.route('/api/admin/add_dataset', methods=['POST'])
def add_dataset():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    question = data.get('question')
    answer = data.get('answer')
    
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO crop_dataset (question, answer) VALUES (:q, :a)"),
                     {"q": question, "a": answer})
    
    return jsonify({'success': True, 'message': '✅ မေးခွန်း-အဖြေ ထည့်ပြီးပါပြီ။'})

@app.route('/api/admin/add_farm', methods=['POST'])
def add_farm():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO farms (farm_id, farm_name, latitude, longitude, current_crop, soil_type, elevation_m, planting_month, harvest_month)
            VALUES (:fid, :fname, :lat, :lon, :crop, :soil, :ele, :plant, :harvest)
        """), {
            "fid": data['farm_id'], "fname": data['farm_name'], 
            "lat": data['latitude'], "lon": data['longitude'],
            "crop": data['current_crop'], "soil": data['soil_type'],
            "ele": data.get('elevation_m', 0), 
            "plant": data.get('planting_month', ''), 
            "harvest": data.get('harvest_month', '')
        })
    
    return jsonify({'success': True, 'message': '✅ စိုက်ခင်းအသစ် ထည့်ပြီးပါပြီ။'})

@app.route('/prices')
def prices_page():
    return render_template('prices.html')

# =======================================================
# 💰 Admin မှ စျေးနှုန်း ပြင်ဆင်ခြင်း API
# =======================================================
@app.route('/api/admin/update_price', methods=['POST'])
def update_price():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    crop_name = data.get('crop_name')
    min_price = data.get('min_price')
    max_price = data.get('max_price')
    
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                UPDATE crop_prices 
                SET min_price = :min_p, max_price = :max_p 
                WHERE crop_name = :c_name
            """), {"min_p": min_price, "max_p": max_price, "c_name": crop_name})
            
            conn.execute(text("""
                INSERT INTO price_history (crop_name, min_price, max_price, recorded_date) 
                VALUES (:c_name, :min_p, :max_p, CURRENT_DATE)
            """), {"c_name": crop_name, "min_p": min_price, "max_p": max_price})
            
        return jsonify({
            'success': True,
            'message': f'✅ {crop_name} ဈေးနှုန်းကို ဒီနေ့အတွက် သိမ်းဆည်းပြီးပါပြီ။'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'❌ Error: {e}'}), 500


@app.route('/api/admin/price_history')
def get_admin_price_history():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        df = pd.read_sql("""
            SELECT id, crop_name, min_price, max_price, 
                   recorded_date::text AS recorded_date, updated_at
            FROM price_history 
            ORDER BY updated_at DESC LIMIT 50
        """, engine)
        df['updated_at'] = df['updated_at'].astype(str)
        return jsonify({"success": True, "data": df.to_dict(orient='records')})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# =======================================================
# 📊 ရွာစာရင်းနှင့် သီးနှံစာရင်း ဇယားအတွက် API များ
# =======================================================
@app.route('/api/all_villages')
def get_all_villages():
    try:
        df = pd.read_sql("SELECT farm_id, farm_name, latitude, longitude, current_crop FROM farms", engine)
        return jsonify({"success": True, "data": df.to_dict(orient='records')})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/all_crops_list')
def get_all_crops_list():
    try:
        df = pd.read_sql("SELECT DISTINCT current_crop FROM farms", engine)
        crops = []
        for _, row in df.iterrows():
            crop = row['current_crop']
            if crop:
                crop_en = crop.split('(')[0].strip()
                crop_mm = crop.split('(')[1].replace(')', '').strip() if '(' in crop else crop_en
                crops.append({"en": crop_en, "mm": crop_mm, "full": crop})
        return jsonify({"success": True, "data": crops})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# =======================================================
# 📄 PDF တင်ရန် နှင့် ဒေါင်းလုဒ်ဆွဲရန် API များ
# =======================================================
@app.route('/api/admin/upload_pdf', methods=['POST'])
def upload_pdf():
    if session.get('role') != 'admin': 
        return jsonify({'error': 'Unauthorized'}), 401
        
    if 'pdf_file' not in request.files: 
        return jsonify({'success': False, 'message': '❌ ဖိုင် မပါဝင်ပါ'}), 400
            
    file = request.files['pdf_file']
    crop_name = request.form.get('crop_name')
        
    if file and file.filename.endswith('.pdf'):
        filename = secure_filename(file.filename)
        save_filename = f"{crop_name}_{filename}" 
        
        try:
            with engine.begin() as conn:
                old_pdfs = conn.execute(text("SELECT pdf_filename FROM crop_pdfs WHERE crop_name = :c"), {"c": crop_name}).fetchall()
                for old_pdf in old_pdfs:
                    old_path = os.path.join(PDF_FOLDER, old_pdf[0])
                    if os.path.exists(old_path):
                        os.remove(old_path)
                
                conn.execute(text("DELETE FROM crop_pdfs WHERE crop_name = :c"), {"c": crop_name})
        except Exception as e:
            print(f"⚠️ Error deleting old PDF: {e}")

        file.save(os.path.join(PDF_FOLDER, save_filename))
            
        with engine.begin() as conn:
            conn.execute(text("INSERT INTO crop_pdfs (crop_name, pdf_filename) VALUES (:c, :f)"), {"c": crop_name, "f": save_filename})
        return jsonify({'success': True, 'message': '✅ PDF ဖိုင် အသစ် တင်ပြီးပါပြီ။ (အဟောင်းကို အလိုအလျောက် ဖျက်ပြီးပါပြီ)'})
    return jsonify({'success': False, 'message': '❌ PDF ဖိုင် သာ တင်ခွင့်ပြုပါသည်။'}), 400

@app.route('/api/get_pdf/<crop_name>')
def get_pdf(crop_name):
    try:
        with engine.begin() as conn:
            result = conn.execute(text("SELECT pdf_filename FROM crop_pdfs WHERE crop_name = :c ORDER BY upload_date DESC LIMIT 1"), {"c": crop_name}).fetchone()
            if result: 
                return jsonify({"success": True, "filename": result[0]})
            else: 
                return jsonify({"success": False})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# =======================================================
# 🌱 မြေအမျိုးအစားအလိုက် သီးနှံ အကြံပြုချက် API
# =======================================================
@app.route('/api/get_crops_by_soil/<soil_name>')
def get_crops_by_soil(soil_name):
    try:
        with engine.connect() as conn:
            query = text("SELECT recommended_crops FROM soil_crop_mapping WHERE soil_type ILIKE :name")
            result = conn.execute(query, {"name": f"%{soil_name}%"}).fetchone()
            
            if result:
                crops_list = [crop.strip() for crop in result[0].split(',')]
                
                crop_images = {
                    "စပါး": "rice.jpg", "လက်ဖက်": "tea.jpg", "ကော်ဖီ": "coffee.jpg",
                    "ပြောင်း": "corn.jpg", "ပဲပုပ်": "soybean.jpg", "ဖရဲသီး": "watermelon.jpg",
                    "စတော်ဘယ်ရီ": "strawberry.jpg", "နာနတ်သီး": "pineapple.jpg",
                    "ရော်ဘာ": "robber.jpg", "မြေပဲ": "peanut.jpg",
                    "ဟင်းသီးဟင်းရွက်": "vegetables.jpg", "သစ်သီးဝလံ": "fruits.jpg"
                }

                soil_details = {
                    "Meadow & Meadow Alluvial Soils": {
                        "mm_name": "မြက်ခင်းနှင့် မြက်ခင်းအနည်ထိုင်မြေ",
                        "image": "soil_meadow.jpg",
                        "desc": "ချိုင်းတွင်းနှင့် လွင်ပြင်တွေမှာ တွေ့ရတယ်။ စပါး၊ ဟင်းသီးဟင်းရွက်နဲ့ ပဲမျိုးစုံ စိုက်ပျိုးနိုင်တယ်။"
                    },
                    "Gley & Gley Swampy Soils": {
                        "mm_name": "ရွံ့ပြာနှင့် ရွံ့ပြာစိမ့်မြေ",
                        "image": "soil_gley.jpg",
                        "desc": "ရေဝပ်တတ်တဲ့ မြေအမျိုးအစားဖြစ်တယ်။ စပါးစိုက်ပျိုးရန် သင့်တော်တယ်။"
                    },
                    "Red Brown Forest Soils": {
                        "mm_name": "နီညိုရောင် သစ်တောမြေ",
                        "image": "soil_red_brown.jpg",
                        "desc": "နီညိုရောင်ရှိပြီး တောင်ကုန်းဒေသတွေမှာ တွေ့ရတယ်။ လက်ဖက်၊ ကော်ဖီနဲ့ သစ်တောပင်တွေ စိုက်ပျိုးနိုင်တယ်။"
                    },
                    "Yellow Brown Forest Soils": {
                        "mm_name": "ဝါညိုရောင် သစ်တောမြေ",
                        "image": "soil_yellow_brown.jpg",
                        "desc": "ဝါညိုရောင်ရှိတဲ့ သစ်တောမြေဖြစ်တယ်။ လက်ဖက်၊ ကော်ဖီနဲ့ သစ်တောပင်တွေ စိုက်ပျိုးနိုင်တယ်။"
                    },
                    "Red Earths & Yellow Earths": {
                        "mm_name": "အနီရောင်နှင့် အဝါရောင်မြေ",
                        "image": "soil_red_earth.jpg",
                        "desc": "အနီရောင်နဲ့ အဝါရောင်ရှိတဲ့ မြေဖြစ်တယ်။ ပြောင်း၊ ပဲပုပ်၊ လက်ဖက်၊ ကော်ဖီနဲ့ စတော်ဘယ်ရီ စိုက်ပျိုးနိုင်တယ်။"
                    },
                    "Mountainous Brown Forest Soils": {
                        "mm_name": "တောင်ပေါ်ဒေသ ညိုရောင်သစ်တောမြေ",
                        "image": "soil_mountain_brown.jpg",
                        "desc": "တောင်မြင့်ဒေသတွေမှာ တွေ့ရတယ်။ သစ်တောပင်တွေ စိုက်ပျိုးနိုင်တယ်။"
                    },
                    "Mountainous Red Forest Soils": {
                        "mm_name": "တောင်ပေါ်ဒေသ အနီရောင်သစ်တောမြေ",
                        "image": "soil_mountain_red.jpg",
                        "desc": "တောင်ပေါ်ဒေသမှာ တွေ့ရတဲ့ အနီရောင်သစ်တောမြေဖြစ်တယ်။ သစ်တောပင်နဲ့ နှစ်ရှည်ပင်တွေ စိုက်ပျိုးနိုင်တယ်။"
                    },
                    "Alluvial": {
                        "mm_name": "အနည်ထိုင်မြေ",
                        "image": "soil_alluvial.jpg",
                        "desc": "မြစ်ချောင်းတွေနားမှာ တွေ့ရတဲ့ အနည်ထိုင်မြေဖြစ်တယ်။ စပါး၊ ပြောင်းနဲ့ ဖရဲသီး စိုက်ပျိုးနိုင်တယ်။"
                    },
                    "Lateritic": {
                        "mm_name": "နီညိုရောင်မြေ (Lateritic)",
                        "image": "soil_lateritic.jpg",
                        "desc": "သံဓာတ်ကြွယ်ဝတဲ့ နီညိုရောင်မြေဖြစ်တယ်။ လက်ဖက်၊ ကော်ဖီ၊ ရော်ဘာနဲ့ နာနတ်သီး စိုက်ပျိုးနိုင်တယ်။"
                    }
                }

                crops_with_images = []
                for crop in crops_list:
                    img = crop_images.get(crop, "default_crop.jpg")
                    crops_with_images.append({"name": crop, "image": img})

                details = soil_details.get(soil_name, {
                    "mm_name": soil_name, 
                    "image": "default_soil.jpg", 
                    "desc": "အချက်အလက် မရှိပါ။"
                })

                return jsonify({
                    "success": True, 
                    "crops": crops_with_images,
                    "soil_image": details["image"],
                    "soil_name_mm": details["mm_name"],
                    "soil_desc": details["desc"]
                })
            else:
                return jsonify({"success": False, "message": "ဒီမြေအမျိုးအစားအတွက် Data မရှိပါ"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/guide')
def user_guide():
    return render_template('guide.html')
@app.route('/about_kengtung')
def about_kengtung():
    return render_template('about_kengtung.html')
# =======================================================
# 📰 စိုက်ပျိုးရေးသတင်းနှင့် ပိုးမွှားရောဂါ API
# =======================================================
@app.route('/api/news', methods=['GET'])
def get_news():
    try:
        df = pd.read_sql("SELECT * FROM agri_news ORDER BY created_at DESC", engine)
        df['created_at'] = df['created_at'].astype(str)
        return jsonify({"success": True, "data": df.to_dict(orient='records')})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/admin/add_news', methods=['POST'])
def add_news():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    title = data.get('title')
    content = data.get('content')
    category = data.get('category', 'General')
    image_url = data.get('image_url', '')
    
    if not title or not content:
        return jsonify({'success': False, 'message': 'ခေါင်းစဉ်နှင့် အကြောင်းအရာ ဖြည့်ပါ'}), 400
        
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO agri_news (title, content, category, image_url) 
                VALUES (:t, :c, :cat, :img)
            """), {"t": title, "c": content, "cat": category, "img": image_url})
        return jsonify({'success': True, 'message': '✅ သတင်း ထည့်သွင်းပြီးပါပြီ။'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'❌ Error: {e}'}), 500

# 👇 ဒါက အရေးကြီးဆုံးပါ (Page ကို ခေါ်ဖို့)
@app.route('/news')
def news_page():
    return render_template('news.html')

# =======================================================
# 📰 သတင်း ပြင်ဆင်ခြင်းနှင့် ဖျက်ခြင်း API
# =======================================================
@app.route('/api/admin/update_news', methods=['POST'])
def update_news():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    news_id = data.get('id')
    title = data.get('title')
    content = data.get('content')
    category = data.get('category')
    image_url = data.get('image_url')
    
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                UPDATE agri_news 
                SET title = :t, content = :c, category = :cat, image_url = :img 
                WHERE id = :id
            """), {"t": title, "c": content, "cat": category, "img": image_url, "id": news_id})
        return jsonify({'success': True, 'message': '✅ သတင်း ပြင်ဆင်ပြီးပါပြီ။'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'❌ Error: {e}'}), 500

@app.route('/api/admin/delete_news', methods=['POST'])
def delete_news():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    news_id = data.get('id')
    
    try:
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM agri_news WHERE id = :id"), {"id": news_id})
        return jsonify({'success': True, 'message': '✅ သတင်း ဖျက်ပြီးပါပြီ။'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'❌ Error: {e}'}), 500

# =======================================================
# 📚 Dataset ပြင်ဆင်ခြင်းနှင့် ဖျက်ခြင်း API
# =======================================================
@app.route('/api/admin/update_dataset', methods=['POST'])
def update_dataset():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    dataset_id = data.get('id')
    question = data.get('question')
    answer = data.get('answer')
    
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                UPDATE crop_dataset 
                SET question = :q, answer = :a 
                WHERE id = :id
            """), {"q": question, "a": answer, "id": dataset_id})
        return jsonify({'success': True, 'message': '✅ Dataset ပြင်ဆင်ပြီးပါပြီ။'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'❌ Error: {e}'}), 500

@app.route('/api/admin/delete_dataset', methods=['POST'])
def delete_dataset():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    dataset_id = data.get('id')
    
    try:
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM crop_dataset WHERE id = :id"), {"id": dataset_id})
        return jsonify({'success': True, 'message': '✅ Dataset ဖျက်ပြီးပါပြီ။'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'❌ Error: {e}'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
