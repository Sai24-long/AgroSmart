import json
import csv
import os

# ⚠️ သင့် JSON ဖိုင်နာမည်ကို ဒီမှာ ထည့်ပါ
json_file_path = 'gemini-code-1793284427705.json' 

# သိမ်းမယ့် CSV ဖိုင် (သင့် db_setup.py က ဒီဖိုင်ကို ရှာနေပါတယ်)
csv_file_path = 'data/crop_data.csv'

# data folder မရှိရင် ဆောက်မယ်
os.makedirs('data', exist_ok=True)

try:
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # CSV ဖိုင်ကို ဖွင့်ပြီး ရေးမယ်
    with open(csv_file_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        # Header ရေးမယ် (db_setup.py က Question နဲ့ Answer ကို ရှာနေတာမို့ ဒီအတိုင်း ထားရပါမယ်)
        writer.writerow(['Question', 'Answer'])

        count = 0
        for category_data in data:
            for qa in category_data.get('qa_list', []):
                question = qa.get('q', '')
                answer = qa.get('a', '')
                writer.writerow([question, answer])
                count += 1

    print(f"✅ အောင်မြင်စွာ ပြောင်းလဲပြီးပါပြီ။")
    print(f"📁 ဖိုင်တည်နေရာ: {csv_file_path}")
    print(f"📊 စုစုပေါင်း မေးခွန်း-အဖြေ: {count} ခု")

except Exception as e:
    print(f"❌ Error ဖြစ်သွားပါတယ်: {e}")