import pandas as pd

df = pd.read_csv('data/weather_kengtung_2020_2024.csv')

print("=" * 50)
print("📊 DATA SUMMARY")
print("=" * 50)

print(f"\n✅ Total rows: {len(df)}")
print(f"✅ First date: {df['date'].min()}")
print(f"✅ Last date:  {df['date'].max()}")

print(f"\n📅 Years covered:")
df['year'] = df['date'].astype(str).str[:4]
print(df['year'].value_counts().sort_index())

print(f"\n📋 Columns: {list(df.columns)}")
print(f"\n🔍 Missing values:")
print(df.isnull().sum())