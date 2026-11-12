from flask import Flask, render_template, request, jsonify
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

# 1. Dataset ကို ဖတ်မယ်
try:
    # encoding='utf-8' ကို ထည့်ဖို့ လိုပါတယ် (မြန်မာစာအတွက်)
    df = pd.read_csv('data/crop_data.csv', encoding='utf-8')
    
    # Question တွေကို Vector ပြောင်းဖို့ TF-IDF ကို အသုံးပြုမယ်
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(df['Question'])
    print("✅ Dataset loaded successfully!")
except Exception as e:
    print(f"⚠️ Dataset loading error: {e}")
    df = None

@app.route('/')
def home():
    return render_template('chat_similarity.html')

@app.route('/api/chat_similarity', methods=['POST'])
def chat():
    if df is None:
        return jsonify({'error': 'Dataset not loaded properly.'}), 500

    data = request.json
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({'error': 'Message is empty'}), 400

    try:
        # 2. အသုံးပြုသူ မေးလိုက်တဲ့ စာသားကို Vector ပြောင်းမယ်
        user_vec = vectorizer.transform([user_message])
        
        # 3. Cosine Similarity တွက်မယ်
        similarities = cosine_similarity(user_vec, tfidf_matrix).flatten()
        
        # 4. အမြင့်ဆုံး Similarity ရှိတဲ့ Index ကို ရှာမယ်
        best_match_idx = similarities.argmax()
        best_score = similarities[best_match_idx]
        
        # အကယ်၍ Similarity က 0.1 အောက် နည်းနေရင် ပြန်ဖြေမယ်
        if best_score < 0.1:
            return jsonify({'reply': "တောင်းပန်ပါတယ်။ အဲ့ဒီမေးခွန်းအတွက် အဖြေကို ကျွန်တော် မသိသေးပါဘူး။ အခြားမေးခွန်းတစ်ခု မေးကြည့်ပါ။"})
        
        # 5. အဖြေကို ယူမယ်
        best_answer = df.iloc[best_match_idx]['Answer']
        
        return jsonify({'reply': best_answer})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5002) # Port 5002 ကို သုံးထားပါတယ်