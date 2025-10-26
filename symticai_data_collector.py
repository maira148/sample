import os
import json
import time
from datetime import datetime
from apify_client import ApifyClient

# =====================================
# CONFIGURATION
# =====================================
API_TOKEN = "apify_api_f1TuMhI5X1f6ZXH4XT2sVpmQeBGh8c45myK3"  # your Apify token
DATA_DIR = "data"
MAX_RESULTS = 100
RETRY_LIMIT = 3

os.makedirs(DATA_DIR, exist_ok=True)
client = ApifyClient(API_TOKEN)


# =====================================
# Helper Functions
# =====================================
def save_json(file_name, data):
    """Save data to JSON file."""
    path = os.path.join(DATA_DIR, file_name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"✅ Data saved to: {path}")


def collect_from_apify(actor_id, run_input, platform_name):
    """Run Apify actor and save data."""
    print(f"\n🚀 Collecting data for {platform_name}...")

    for attempt in range(1, RETRY_LIMIT + 1):
        try:
            run = client.actor(actor_id).call(run_input=run_input)
            dataset_id = run.get("defaultDatasetId")
            items = [item for item in client.dataset(dataset_id).iterate_items()]

            # Limit results just in case actor returns more
            items = items[:MAX_RESULTS]
            save_json(f"{platform_name.lower()}_raw.json", items)

            print(f"✅ {platform_name}: {len(items)} items collected.")
            return len(items)

        except Exception as e:
            print(f"⚠️ Attempt {attempt} failed for {platform_name}: {e}")
            if attempt < RETRY_LIMIT:
                print("⏳ Retrying in 5 seconds...")
                time.sleep(5)
            else:
                print(f"❌ Failed to collect data for {platform_name} after {RETRY_LIMIT} attempts.")
                return 0


# =====================================
# SCRAPERS CONFIGURATION
# =====================================

# Instagram Scraper
instagram_actor = "apify/instagram-scraper"
instagram_input = {
    "directUrls": [
        "https://www.instagram.com/nasa/",
        "https://www.instagram.com/9gag/",
        "https://www.instagram.com/natgeo/",
    ],
    "resultsType": "posts",
    "resultsLimit": MAX_RESULTS,
    "addParentData": False,
}

# TikTok Scraper
tiktok_actor = "clockworks/tiktok-scraper"
tiktok_input = {
    "profiles": [
        "https://www.tiktok.com/@nba",
        "https://www.tiktok.com/@tech",
        "https://www.tiktok.com/@fashion",
    ],
    "maxResults": MAX_RESULTS,
    "downloadVideos": False,
}

# Facebook Scraper
facebook_actor = "apify/facebook-posts-scraper"
facebook_input = {
    "startUrls": [
        {"url": "https://www.facebook.com/nasa"},
        {"url": "https://www.facebook.com/9gag"},
        {"url": "https://www.facebook.com/NationalGeographic"},
    ],
    "maxItems": MAX_RESULTS,
}

# =====================================
# EXECUTION
# =====================================
summary = {}
summary["Instagram"] = collect_from_apify(instagram_actor, instagram_input, "Instagram")
summary["TikTok"] = collect_from_apify(tiktok_actor, tiktok_input, "TikTok")
summary["Facebook"] = collect_from_apify(facebook_actor, facebook_input, "Facebook")

# =====================================
# TIMESTAMP + SUMMARY LOG
# =====================================
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
timestamp_file = os.path.join(DATA_DIR, "last_update.txt")

with open(timestamp_file, "w") as f:
    f.write(f"Last update: {timestamp}\n\n")
    f.write(json.dumps(summary, indent=4))

print("\n🕒 Data collection completed successfully for all platforms!")
print(f"📅 Timestamp: {timestamp}")
print(f"📊 Summary: {summary}")
