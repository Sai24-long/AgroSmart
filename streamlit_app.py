import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import joblib
import plotly.express as px

# ⚠️ သင့် PostgreSQL Password ကို ဒီမှာ ထည့်ပါ
DB_PASSWORD = 'root' 

engine = create_engine(f'postgresql://postgres:{DB_PASSWORD}@localhost:5432/agro_db')

st.set_page_config(page_title="Agro Advisory System", layout="wide", page_icon="🌾")
st.title("🌾 ကျိုင်းတုံ စိုက်ပျိုးရေး အကြံပြုစနစ်")

# Data ဆွဲထုတ်မယ်
@st.cache_data
def load_data():
    farms = pd.read_sql("SELECT * FROM farms", engine)
    guides = pd.read_sql("SELECT * FROM crop_guides", engine)
    weather = pd.read_sql("SELECT * FROM weather_data", engine)
    return farms, guides, weather

try:
    df_farms, df_guides, df_weather = load_data()
except Exception as e:
    st.error(f"Database ချိတ်ဆက်မှု မအောင်မြင်ပါ: {e}")
    st.stop()

# ML Model ကို ခေါ်မယ်
try:
    ml_model = joblib.load('crop_model.pkl')
except:
    ml_model = None

# Sidebar မှာ စိုက်ခင်း ရွေးမယ်
st.sidebar.header("📍 စိုက်ခင်း ရွေးချယ်ပါ")
selected_farm_name = st.sidebar.selectbox("စိုက်ခင်းစာရင်း", df_farms['farm_name'])
farm_info = df_farms[df_farms['farm_name'] == selected_farm_name].iloc[0]
crop_keyword = farm_info['current_crop']

# Main Layout (၂ ကော်လံ ခွဲမယ်)
col1, col2 = st.columns([1, 2])

# === ဘယ်ဘက်ကော်လံ (ပုံနဲ့ မြေပုံ) ===
with col1:
    st.subheader("📸 သီးနှံပုံ")
    if 'Rice' in crop_keyword:
        st.image("https://images.unsplash.com/photo-1586201375761-83865001e31c?auto=format&fit=crop&w=500&q=80", caption="စပါး")
    elif 'Tea' in crop_keyword:
        st.image("https://images.unsplash.com/photo-1597318181409-cf64d0b5d8a2?auto=format&fit=crop&w=500&q=80", caption="လက်ဖက်")
    elif 'Pineapple' in crop_keyword:
        st.image("https://images.unsplash.com/photo-1550258987-190a2d41a8ba?auto=format&fit=crop&w=500&q=80", caption="နာနတ်သီး")
    elif 'Strawberry' in crop_keyword:
        st.image("https://images.unsplash.com/photo-1464965911861-746a04b4bca6?auto=format&fit=crop&w=500&q=80", caption="စတော်ဘယ်ရီ")
    elif 'Peanut' in crop_keyword:
        st.image("https://images.unsplash.com/photo-1567892737950-30c4db37cd89?auto=format&fit=crop&w=500&q=80", caption="မြေပဲ")
    elif 'Corn' in crop_keyword:
        st.image("https://images.unsplash.com/photo-1551754655-cd27e38d2076?auto=format&fit=crop&w=500&q=80", caption="ပြောင်း")
    else:
        st.info("ပုံ မရှိပါ")
        
    st.markdown("---")
    st.subheader("📍 တည်နေရာ")
    map_data = pd.DataFrame({'lat': [farm_info['latitude']], 'lon': [farm_info['longitude']]})
    st.map(map_data, zoom=11)

# === ညာဘက်ကော်လံ (အချက်အလက်နဲ့ ဂရပ်ဖ်) ===
with col2:
    st.subheader(f"🏡 {farm_info['farm_name']}")
    m1, m2, m3 = st.columns(3)
    m1.metric("သီးနှံ", crop_keyword.split('(')[0].strip())
    m2.metric("အမြင့်", f"{farm_info['elevation_m']} m")
    m3.metric("မြေအမျိုးအစား", farm_info['soil_type'])
    
    st.markdown("---")
    st.subheader("🌤️ မိုးလေဝသအခြေအနေ (၂၀၂၄ ခုနှစ်)")
    
    # ရာသီဥတု ဂရပ်ဖ် ဆွဲမယ်
    df_2024 = df_weather[df_weather['date'].astype(str).str.startswith('2024')].copy()
    df_2024['date'] = pd.to_datetime(df_2024['date'].astype(str), format='%Y%m%d')
    
    fig = px.line(df_2024, x='date', y='PRECTOTCORR', title='နေ့စဉ် မိုးရေချိန် (mm)', color_discrete_sequence=['blue'])
    st.plotly_chart(fig, use_container_width=True)

# === အောက်ဆုံးမှာ စိုက်ပျိုးနည်းနဲ့ ML ကို ပြမယ် ===
st.markdown("---")
guide_tab, ml_tab = st.tabs(["🌱 စိုက်ပျိုးနည်း", "🤖 ML ခန့်မှန်းချက်"])

with guide_tab:
    guide = None
    for c in df_guides['crop_name']:
        if c in crop_keyword:
            guide = df_guides[df_guides['crop_name'] == c].iloc[0]
            break
            
    if guide is not None:
        c1, c2 = st.columns(2)
        with c1:
            st.success("**အဆင့် ၁ - မြေပြင်ဆင်ခြင်း**")
            st.write(guide['step_1_land_prep'])
            st.info("**အဆင့် ၃ - ပြုစုစောင့်ရှောက်ခြင်း**")
            st.write(guide['step_3_care'])
        with c2:
            st.warning("**အဆင့် ၂ - စိုက်ပျိုးခြင်း**")
            st.write(guide['step_2_planting'])
            st.success("**အဆင့် ၄ - ရိတ်သိမ်းခြင်း**")
            st.write(guide['step_4_harvest'])
    else:
        st.warning("စိုက်ပျိုးနည်း မရှိပါ။")

with ml_tab:
    st.write("မြေဆီလွှာအာဟာရနှင့် ရာသီဥတု ထည့်သွင်းပြီး သီးနှံအမျိုးအစားကို ခန့်မှန်းပါ။")
    if ml_model is not None:
        with st.form("prediction_form"):
            col_a, col_b = st.columns(2)
            with col_a:
                N = st.number_input("N (နိုက်ထရိုဂျင်)", value=90)
                P = st.number_input("P (ဖော့စဖရပ်)", value=42)
                K = st.number_input("K (ပိုတက်စီယမ်)", value=43)
                temp = st.number_input("အပူချိန် (°C)", value=20.8)
            with col_b:
                humidity = st.number_input("စိုထိုင်းဆ (%)", value=82.0)
                ph = st.number_input("မြေ pH", value=6.5)
                rainfall = st.number_input("မိုးရေချိန် (mm)", value=202.9)
                
            submit = st.form_submit_button("🔮 ခန့်မှန်းမည်")
            
            if submit:
                features = pd.DataFrame([[N, P, K, temp, humidity, ph, rainfall]], 
                                        columns=['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall'])
                prediction = ml_model.predict(features)[0]
                st.success(f"✅ ဤမြေဆီလွှာနှင့် ရာသီဥတုအတွက် အသင့်လျော်ဆုံး သီးနှံမှာ **{prediction}** ဖြစ်ပါသည်။")
    else:
        st.error("ML Model (crop_model.pkl) ကို ရှာမတွေ့ပါ။")