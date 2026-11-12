import pandas as pd

# 1. Data ကို ဖတ်မယ်
df = pd.read_csv('data/Crop_recommendation.csv')

# 2. ဘယ်သီးနှံတွေ ပါလဲဆိုတာ ဆွဲထုတ်မယ်
crops = df['label'].unique()

print(f"Kaggle Dataset ထဲမှာ သီးနှံအမျိုးအစား ({len(crops)}) မျိုး ပါတယ် -")
print("-" * 30)
for crop in sorted(crops):
    print(f"✅ {crop}")
print("-" * 30)

# 3. ကျွန်တော်တို့ လိုချင်တဲ့ သီးနှံတွေ ပါမပါ စစ်မယ်
target_crops = ['peanut', 'groundnut', 'pineapple', 'strawberry', 'watermelon', 'rice', 'maize']

print("\nကျွန်တော်တို့ ဒေသထွက် သီးနှံတွေ ပါမပါ စစ်ဆေးချက် -")
for target in target_crops:
    if target in crops:
        print(f"🟢 {target} - ပါတယ် (Model က ခန့်မှန်းနိုင်မယ်)")
    else:
        print(f"🔴 {target} - မပါဘူး (Model က ခန့်မှန်းနိုင်မှာ မဟုတ်ဘူး)")