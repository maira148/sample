import subprocess
import os
import json
import time
from pymongo import MongoClient
from datetime import datetime

# ===============================
# CONFIGURATION
# ===============================
DATA_DIR = "data"
PREDICTIONS_DIR = "predictions"
MONGO_URI = "mongodb://localhost:27017/"  # Replace with hosted MongoDB URI
DB_NAME = "trending_data"

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
raw_collection = db["raw_posts"]
pred_collection = db["predictions"]

# JSON files mapping
raw_files = {
    "Instagram": os.path.join(DATA_DIR, "instagram_raw.json"),
    "TikTok": os.path.join(DATA_DIR, "tiktok_raw.json"),
    "Facebook": os.path.join(DATA_DIR, "facebook_raw.json"),
}

prediction_files = {
    "Instagram": os.path.join(PREDICTIONS_DIR, "instagram_trends.json"),
    "TikTok": os.path.join(PREDICTIONS_DIR, "tiktok_trends.json"),
    "Facebook": os.path.join(PREDICTIONS_DIR, "facebook_trends.json"),
    "Combined": os.path.join(PREDICTIONS_DIR, "combined_trends.json"),
}

# Helper function to insert JSON into MongoDB
def insert_json_to_mongo(file_path, collection, platform_name, timestamp_field):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            items = json.load(f)
            for item in items:
                item["platform"] = platform_name
                item[timestamp_field] = datetime.utcnow()
            if items:
                collection.insert_many(items)
            print(f"✅ {len(items)} {platform_name} items inserted into MongoDB.")
    else:
        print(f"⚠️ File not found: {file_path}")

# ===============================
# MAIN LOOP (runs every 24h)
# ===============================
INTERVAL = 24 * 60 * 60  # 24 hours in seconds

while True:
    print("🚀 Starting data collection...")
    subprocess.run(["python", "data_collection.py"], check=True)

    # Insert raw data into MongoDB
    for platform, path in raw_files.items():
        insert_json_to_mongo(path, raw_collection, platform, "collected_at")

    print("🚀 Starting prediction...")
    subprocess.run(["python", "prediction.py"], check=True)

    # Insert prediction data into MongoDB
    for platform, path in prediction_files.items():
        insert_json_to_mongo(path, pred_collection, platform, "predicted_at")

    print(f"⏳ Waiting 24 hours for the next run...")
    time.sleep(INTERVAL)
