from sqlalchemy import create_engine
import pandas as pd

# ⚠️ သင့် PostgreSQL Password ကို ဒီမှာ ထည့်ပါ
DB_PASSWORD = 'root' 
engine = create_engine(f'postgresql://postgres:{DB_PASSWORD}@localhost:5432/agro_db')

try:
    # Column တွေကို စစ်ဆေးခြင်း
    df = pd.read_sql("SELECT * FROM crop_params LIMIT 1", engine)
    print("✅ သင့် Database ထဲက Column နာမည်များ -")
    print(df.columns.tolist())
except Exception as e:
    print(f"❌ Error: {e}")