import os
import json
import re
import math
import time
from datetime import datetime
from collections import defaultdict

# =========================
# CONFIGURATION
# =========================
DATA_DIR = "data"
PREDICTIONS_DIR = "predictions"
os.makedirs(PREDICTIONS_DIR, exist_ok=True)

INSTAGRAM_FILE = os.path.join(DATA_DIR, "instagram_raw.json")
TIKTOK_FILE = os.path.join(DATA_DIR, "tiktok_raw.json")
FACEBOOK_FILE = os.path.join(DATA_DIR, "facebook_raw.json")

TOP_N = 10  # Top N trends per platform

# =========================
# HELPER FUNCTIONS
# =========================
def load_json(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️ File not found: {file_path}")
        return []

def save_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"✅ Saved: {file_path}")

def normalize_scores(score_dict):
    if not score_dict:
        return {}
    max_score = max(score_dict.values())
    if max_score == 0:
        return {k: 0 for k in score_dict}
    return {k: v / max_score for k, v in score_dict.items()}

def score_to_category(score):
    if score >= 0.7:
        return "HIGH"
    elif score >= 0.4:
        return "MEDIUM"
    else:
        return "LOW"

def predict_next_24h(score):
    """Simple non-linear growth prediction model"""
    base = 50_000_000  # baseline engagement scale
    predicted = base * (score ** 1.2)
    return round(predicted)

def extract_timestamp(ts):
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
    except Exception:
        return time.time()

def exponential_decay_weight(hours_ago, half_life=12):
    """Weight decreases exponentially with time"""
    return math.exp(-math.log(2) * (hours_ago / half_life))

# =========================
# FACEBOOK HASHTAG GENERATOR
# =========================
def generate_hashtags_from_text(text):
    """Generate hashtags from meaningful keywords in the text."""
    text = text.lower()
    words = re.findall(r'\b[a-z]{4,}\b', text)
    ignore = {
        "https", "http", "about", "learn", "more", "that", "with", "have", "been",
        "there", "this", "from", "they", "them", "their", "you", "your", "when",
        "where", "what", "which", "also", "into", "some", "like", "than", "then",
        "after", "such", "being", "just", "make", "take", "over", "while", "still"
    }
    keywords = [w for w in words if w not in ignore]
    hashtags = set()
    for i in range(len(keywords) - 1):
        hashtags.add(f"#{keywords[i]}")
        hashtags.add(f"#{keywords[i]}{keywords[i+1]}")
    return list(hashtags)[:5]

# =========================
# INSTAGRAM
# =========================
def process_instagram(instagram_data):
    now = time.time()
    hashtag_scores = defaultdict(float)
    hashtag_posts = defaultdict(list)

    for post in instagram_data:
        hashtags = post.get("hashtags", [])
        engagement = post.get("commentsCount", 0)
        ts = extract_timestamp(post.get("timestamp", datetime.utcnow().isoformat()))
        hours_ago = (now - ts) / 3600
        weight = exponential_decay_weight(hours_ago)
        url = post.get("url", "")

        for h in hashtags:
            weighted = engagement * weight
            hashtag_scores[h] += weighted
            hashtag_posts[h].append({"url": url, "engagement": engagement})

    normalized = normalize_scores(hashtag_scores)
    top_trends = sorted(normalized.items(), key=lambda x: x[1], reverse=True)[:TOP_N]

    results = []
    for h, s in top_trends:
        results.append({
            "platform": "Instagram",
            "hashtag": h,
            "score": s,
            "predicted_trend": score_to_category(s),
            "predicted_engagement_next_24h": predict_next_24h(s),
            "top_posts": hashtag_posts[h]
        })
    return results

# =========================
# TIKTOK
# =========================
def process_tiktok(tiktok_data):
    now = time.time()
    hashtag_scores = defaultdict(float)
    hashtag_posts = defaultdict(list)

    for post in tiktok_data:
        hashtags = [h.get("name") for h in post.get("hashtags", []) if h.get("name")]
        engagement = post.get("diggCount", 0) + post.get("shareCount", 0) + post.get("commentCount", 0)
        ts = extract_timestamp(post.get("createTimeISO", datetime.utcnow().isoformat()))
        hours_ago = (now - ts) / 3600
        weight = exponential_decay_weight(hours_ago)
        url = post.get("webVideoUrl", "")

        for h in hashtags:
            weighted = engagement * weight
            hashtag_scores[h] += weighted
            hashtag_posts[h].append({"url": url, "engagement": engagement})

    normalized = normalize_scores(hashtag_scores)
    top_trends = sorted(normalized.items(), key=lambda x: x[1], reverse=True)[:TOP_N]

    results = []
    for h, s in top_trends:
        results.append({
            "platform": "TikTok",
            "hashtag": h,
            "score": s,
            "predicted_trend": score_to_category(s),
            "predicted_engagement_next_24h": predict_next_24h(s),
            "top_posts": hashtag_posts[h]
        })
    return results

# =========================
# FACEBOOK
# =========================
def process_facebook(facebook_data):
    now = time.time()
    hashtag_scores = defaultdict(float)
    hashtag_posts = defaultdict(list)

    for post in facebook_data:
        text = post.get("text", "")
        engagement = post.get("likes", 0) + post.get("comments", 0) + post.get("shares", 0)
        ts = post.get("time") or post.get("timestamp")
        if isinstance(ts, str):
            ts = extract_timestamp(ts)
        elif isinstance(ts, (int, float)):
            ts = float(ts)
        hours_ago = (now - ts) / 3600 if ts else 24
        weight = exponential_decay_weight(hours_ago)
        url = post.get("url", "")

        # Extract or generate hashtags
        text_hashtags = [w.strip("#") for w in text.split() if w.startswith("#")]
        if not text_hashtags:
            text_hashtags = [h.strip("#") for h in generate_hashtags_from_text(text)]

        for h in text_hashtags:
            weighted_score = engagement * weight
            hashtag_scores[h] += weighted_score
            hashtag_posts[h].append({
                "url": url,
                "engagement": engagement,
                "hours_ago": round(hours_ago, 2)
            })

    normalized = normalize_scores(hashtag_scores)
    top_trends = sorted(normalized.items(), key=lambda x: x[1], reverse=True)[:TOP_N]

    results = []
    for h, s in top_trends:
        results.append({
            "platform": "Facebook",
            "hashtag": h,
            "score": s,
            "predicted_trend": score_to_category(s),
            "predicted_engagement_next_24h": predict_next_24h(s),
            "top_posts": hashtag_posts[h]
        })
    return results

# =========================
# COMBINE TRENDS
# =========================
def combine_trends(insta, tiktok, fb):
    combined_scores = defaultdict(float)
    combined_posts = defaultdict(list)
    hashtag_platforms = defaultdict(set)

    for trend_list in [insta, tiktok, fb]:
        for t in trend_list:
            h = t["hashtag"]
            combined_scores[h] += t["score"]
            combined_posts[h].extend(t["top_posts"])
            hashtag_platforms[h].add(t["platform"])

    top_combined = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)[:TOP_N]
    results = []
    for h, s in top_combined:
        results.append({
            "hashtag": h,
            "predicted_trend": score_to_category(s),
            "combined_score": s,
            "predicted_engagement_next_24h": predict_next_24h(s),
            "likely_platforms": list(hashtag_platforms[h]),
            "top_posts": combined_posts[h][:3]
        })
    return results

# =========================
# MAIN
# =========================
def main():
    print("🔹 Loading data...")
    insta_data = load_json(INSTAGRAM_FILE)
    tiktok_data = load_json(TIKTOK_FILE)
    fb_data = load_json(FACEBOOK_FILE)

    print("🔹 Processing platforms...")
    insta_trends = process_instagram(insta_data)
    tiktok_trends = process_tiktok(tiktok_data)
    fb_trends = process_facebook(fb_data)

    save_json(os.path.join(PREDICTIONS_DIR, "instagram_trends.json"), insta_trends)
    save_json(os.path.join(PREDICTIONS_DIR, "tiktok_trends.json"), tiktok_trends)
    save_json(os.path.join(PREDICTIONS_DIR, "facebook_trends.json"), fb_trends)

    print("🔹 Combining cross-platform trends...")
    combined = combine_trends(insta_trends, tiktok_trends, fb_trends)
    save_json(os.path.join(PREDICTIONS_DIR, "combined_trends.json"), combined)

    print("\n✅ Trend prediction completed! Combined results saved in predictions/combined_trends.json")

if __name__ == "__main__":
    main()






