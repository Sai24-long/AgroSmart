import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib

# ၁။ Data ဖတ်
df = pd.read_csv('data/Crop_recommendation.csv')

print("Dataset shape:", df.shape)
print("Crops:", df['label'].unique())
print("Number of crops:", df['label'].nunique())

# ၂။ Features နဲ့ Target ခွဲ
X = df[['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']]
y = df['label']

# ၃။ Train/Test Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# ၄။ Model ဆောက်
model = RandomForestClassifier(
    n_estimators=100,
    max_depth=15,
    random_state=42
)

# ၅။ Train
print("\nTraining...")
model.fit(X_train, y_train)

# ၆။ Evaluate
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)

print(f"\n✅ Accuracy: {accuracy * 100:.2f}%")
print("\n", classification_report(y_test, y_pred))

# ၇။ Model သိမ်း
joblib.dump(model, 'crop_model.pkl')
print("\n✅ Model saved: crop_model.pkl")

# ၈။ Test — ဥပမာ
sample = [[90, 42, 43, 20.8, 82.0, 6.5, 202.9]]
prediction = model.predict(sample)
print(f"\n🔮 Sample prediction: {prediction[0]}")