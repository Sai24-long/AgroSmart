import pandas as pd
import os

print("⏳ ကျိုင်းတုံဒေသခံ Spatial Data ဖန်တီးနေသည်...")

# 1. စိုက်ခင်း ၂၉ ခု (အမြင့် elevation_m ပါဝင်သည်)
farms_data = {
    'farm_id': [
        'F001', 'F002', 'F003', 'F004', 'F005', 
        'F006', 'F007', 'F008', 'F009', 'F010', 
        'F011', 'F012', 'F013', 'F014', 'F015', 
        'F016', 'F017', 'F018', 'F019', 'F020', 
        'F021', 'F022', 'F023', 'F024', 'F025',
        'F026', 'F027', 'F028', 'F029'
    ],
    
    'farm_name': [
        'Jian Lake Village (ကျိုင်းလိတ်ရွာ)',
        'Wan Gwen Village (ဝမ်ကောင်းရွာ)',
        'Kadtao Village (ကတ်တောင်ရွာ)',
        'Mong Zin Village (မိုင်းဇင်းရွာ)',
        'Yar Nyunt Farm (ယာညွန့်လယ်ယာခြံ)',
        'Wan Hsai Tea Garden (ဝမ်ဆိုင်းလွယ်ရွာ)', 
        'U Shout Ti Green Tea Garden (ဦးရှောက်တိလက်ဖက်စိမ်းခြံ)',
        'Pang-Wai Green Tea Farm (ပန်ဝိုင်လက်ဖက်ခြံ)',
        'Pang-Wai Coffee Farm (ပန်ဝိုင်ကော်ဖီခြံ)',
        'Kengtung Agri Research Farm', 
        'Wan Jiang Lake Village (ဝမ်ကျိုင်းလိတ်ရွာ)',
        'Wan Kart Htai (ကတ်ထိုက်ရွာ)',   
        'Loi Mwe Pineapple Farm(လွယ်မွေနာနတ်သီးခြံ)', 
        'Pang Koi Near Pineapple Farm (ပန်ကွဲနာနတ်သီးခြံ)',     
        'Loi Mwe Strawberry Farm (လွယ်မွေစတော်ဘယ်ရီခြံ)',       
        'Pang Koi Near Strawberry Farm (ပန်ကွဲစတော်ဘယ်ရီခြံ)',
        'Yang Hla Village Rubber Farm (ယန်းလှရော်ဘာခြံ)',
        'Loi Mwe Crab Apple Farm (လွယ်မွေပင်စိမ်းသီးခြံ)', 
        'Pang Koi Crab Apple Farm (ပန်ကွဲပင်စိမ်းသီးခြံ)',
        'Loi Mwe Damson (လွယ်မွေမက်မန်းသီးခြံ)',
        'Kyaing Tong Hilltop Area',
        'Pang Koi Coffee Farm (ပန်ကွဲကော်ဖီခြံ)',
        'Mong Lan Village (မိုင်းလန်ရွာ)', # ဒီနေရာမှာ ကော်မာ ဖြည့်ထားပါတယ်
        'Ping Tauk Panlay Ann Village(ပင်းတောက်ပန်လေအန်းရွာ)',
        'Nam Latt Valley (နမ့်လတ်ချောင်း)',
        'Mong Khun Village (မိုင်းခွန်ရွာ)',
        'Arr Khay Village (အားခေရွာ)',
        'Mong Lat Village (မိုင်းလပ်)',
        'Mong Lat Village (မိုင်းလပ်)'
    ],
    
    'latitude': [
        21.31986, 21.32363, 21.38923, 21.36141, 21.14201, 
        21.36064, 21.16932, 21.19781, 21.19769, 21.19703, 
        21.31986, 21.43967, 21.18943, 21.16296, 21.18962, 
        21.16327, 21.32247, 21.18962, 21.16329, 21.18992, 
        21.17488, 21.16429, 21.32276, 21.44050, 21.25050,
        21.28303, 21.28423, 21.28425, 21.28430
    ],
    
    'longitude': [
        99.63653, 99.55151, 99.60302, 99.64980, 99.72753, 
        99.64249, 99.60101, 99.75241, 99.75297, 99.6100, 
        99.63653, 99.58477, 99.76527, 99.73058, 99.76530, 
        99.73042, 99.62959, 99.76530, 99.73042, 99.76560, 
        99.72234, 99.73042, 99.70174, 99.58280, 99.67878,
        99.62362, 99.63307, 99.63207, 99.63217
    ],
    
    'elevation_m': [
        1200, 1200, 1200, 1250, 2500, 
        2600, 2500, 2500, 1100, 1300, 
        1400, 2700, 2400, 2400, 2400, 
        2400, 1200, 2400, 2400, 2400, 
        2400, 2400, 2400, 1200, 1200,
        1200, 1200, 2400, 2400
    ],
    
    'soil_type': [
        'Alluvial', 'Alluvial', 'Alluvial', 'Alluvial', 'Lateritic', 
        'Lateritic', 'Lateritic', 'Lateritic', 'Lateritic', 'Alluvial', 
        'Alluvial', 'Lateritic', 'Lateritic', 'Lateritic', 'Lateritic', 
        'Lateritic', 'Alluvial', 'Lateritic', 'Lateritic', 'Lateritic', 
        'Lateritic', 'Lateritic', 'Lateritic', 'Alluvial', 'Alluvial', # ဒီနေရာက ကော်မာ မှားနေတာ ပြင်ထားပါတယ်
        'Alluvial', 'Alluvial', 'Lateritic', 'Lateritic'
    ],
    
    'current_crop': [
        'Rice (မိုးစပါး)', 
        'Rice (ရေသွင်းသီးထပ်စပါး)', 
        'Rice (မိုးစပါး)', 
        'Rice (နွေစပါး)', 
        'Rice (တောင်ပေါ်စပါး)', 
        'Tea (လက်ဖက်)', 
        'Tea (လက်ဖက်)', 
        'Tea (လက်ဖက်)', 
        'Coffee (ကော်ဖီ)', 
        'Corn (ပြောင်း)', 
        'Watermelon (ဖရဲသီး)', 
        'Peanut (မြေပဲ)', 
        'Pineapple (နာနတ်သီး)', 
        'Pineapple (နာနတ်သီး)', 
        'Strawberry (စတော်ဘယ်ရီ)', 
        'Strawberry (စတော်ဘယ်ရီ)', 
        'Rubber (ရော်ဘာ)', 
        'Crab Apple (ပင်စိမ်းသီး)', 
        'Crab Apple (ပင်စိမ်းသီး)', 
        'Damson/Plum (မက်မန်းသီး)', 
        'Damson/Plum (မက်မန်းသီး)',
        'Coffee (ကော်ဖီ)',
        'Rubber (ရော်ဘာ)',
        'Rice (ရေသွင်းသီးထပ်စပါး)',
        'Rice (နွေစပါး)', 
        'Rice (နွေစပါး)',
        'Rice (မိုးစပါး)',
        'Corn (ပြောင်း)',
        'Peanut (မြေပဲ)'
    ],
    
    'planting_month': [
        'June (ဇွန်)', 
        'Year-round (တစ်နှစ်ပတ်လုံး)', 
        'May-June (မေ-ဇွန်)', 
        'December-January (ဒီဇင်ဘာ-ဇန်နဝါရီ)', 
        'May (မေ)', 
        'June (ဇွန်)', 
        'September (စက်တင်ဘာ)', 
        'October (အောက်တိုဘာ)', 
        'June-July (ဇွန်-ဇူလိုင်)', 
        'May-June (မေ-ဇွန်)', 
        'October-November (အောက်တိုဘာ-နိုဝင်ဘာ)', 
        'May-June (မေ-ဇွန်)', 
        'June-August (ဇွန်-ဩဂုတ်)', 
        'June-August (ဇွန်-ဩဂုတ်)', 
        'September-October (စက်တင်ဘာ-အောက်တိုဘာ)', 
        'September-October (စက်တင်ဘာ-အောက်တိုဘာ)', 
        'June-July (ဇွန်-ဇူလိုင်)', 
        'June-July (ဇွန်-ဇူလိုင်)', 
        'June-July (ဇွန်-ဇူလိုင်)', 
        'June-July (ဇွန်-ဇူလိုင်)', 
        'June-July (ဇွန်-ဇူလိုင်)',
        'June-July (ဇွန်-ဇူလိုင်)',
        'June-July (ဇွန်-ဇူလိုင်)',
        'Year-round (တစ်နှစ်ပတ်လုံး)', 
        'December-January (ဒီဇင်ဘာ-ဇန်နဝါရီ)',
        'December-January (ဒီဇင်ဘာ-ဇန်နဝါရီ)',
        'June (ဇွန်)',
        'May-June (မေ-ဇွန်)',
        'May-June (မေ-ဇွန်)'
    ],
    
    'harvest_month': [
        'November (နိုဝင်ဘာ)', 
        'Year-round (တစ်နှစ်ပတ်လုံး)', 
        'October-November (အောက်တိုဘာ-နိုဝင်ဘာ)', 
        'April-May (ဧပြီ-မေ)', 
        'October (အောက်တိုဘာ)', 
        'December (ဒီဇင်ဘာ)', 
        'January (ဇန်နဝါရီ)', 
        'February (ဖေဖော်ဝါရီ)', 
        'November-February (နိုဝင်ဘာ-ဖေဖော်ဝါရီ)', 
        'September-October (စက်တင်ဘာ-အောက်တိုဘာ)', 
        'January-March (ဇန်နဝါရီ-မတ်)', 
        'September-October (စက်တင်ဘာ-အောက်တိုဘာ)', 
        'May-July (မေ-ဇူလိုင်)', 
        'May-July (မေ-ဇူလိုင်)', 
        'December-March (ဒီဇင်ဘာ-မတ်)', 
        'December-March (ဒီဇင်ဘာ-မတ်)', 
        'September-April (စက်တင်ဘာ-ဧပြီ)', 
        'September-November (စက်တင်ဘာ-နိုဝင်ဘာ)', 
        'September-November (စက်တင်ဘာ-နိုဝင်ဘာ)', 
        'May-July (မေ-ဇူလိုင်)', 
        'May-July (မေ-ဇူလိုင်)',
        'November-February (နိုဝင်ဘာ-ဖေဖော်ဝါရီ)',
        'September-April (စက်တင်ဘာ-ဧပြီ)',
        'Year-round (တစ်နှစ်ပတ်လုံး)', 
        'April-May (ဧပြီ-မေ)',
        'April-May (ဧပြီ-မေ)',
        'November (နိုဝင်ဘာ)',
        'September-October (စက်တင်ဘာ-အောက်တိုဘာ)', 
        'May-July (မေ-ဇူလိုင်)'
    ]
}

# 2. မိုးလေဝသစခန်း ၅ ခု (ID နဲ့ Data အရေအတွက် ညှိထားပါတယ်)
stations_data = {
    'station_id': ['S001', 'S002', 'S003', 'S004', 'S005'],
    'station_name': ['Kengtung Center', 'Kengtung Airport', 'Kengtung East', 'Loi Mwe', 'Pang Koi'],
    'latitude': [21.28705, 21.30190, 21.2850, 21.16768, 21.16035],
    'longitude': [99.60005, 99.6188, 99.5950, 99.74694, 99.74075]
}

# Folder မရှိရင် ဆောက်
os.makedirs('data', exist_ok=True)

# CSV အနေနဲ့ သိမ်း
df_farms = pd.DataFrame(farms_data)
df_stations = pd.DataFrame(stations_data)

# ဖိုင်နာမည်တွေကို သင့်တောင်းဆိုချက်အတိုင်း ပြောင်းထားပါတယ်
df_farms.to_csv('data/farms_locations.csv', index=False, encoding='utf-8-sig')
df_stations.to_csv('data/weather_stations.csv', index=False, encoding='utf-8-sig')

print("✅ data/farms_locations.csv ကို ဆောက်ပြီးပါပြီ (စိုက်ခင်း ၂၉ ခု)")
print("✅ data/weather_stations.csv ကို ဆောက်ပြီးပါပြီ (မိုးလေဝသစခန်း ၅ ခု)")