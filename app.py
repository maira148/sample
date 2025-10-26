import os
import json
import subprocess
import streamlit as st
from datetime import datetime

# =========================
# CONFIGURATION
# =========================
st.set_page_config(
    page_title="Social Media Trend Forecast",
    layout="wide",
    page_icon="📊",
)

DATA_DIR = "predictions"
PLATFORMS = ["Instagram", "TikTok", "Facebook", "Combined"]

# =========================
# HELPERS
# =========================
def load_json(file_path):
    if not os.path.exists(file_path):
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_file_for_platform(platform):
    mapping = {
        "Instagram": "instagram_trends.json",
        "TikTok": "tiktok_trends.json",
        "Facebook": "facebook_trends.json",
        "Combined": "combined_trends.json",
    }
    return os.path.join(DATA_DIR, mapping[platform])

def render_trend_card(trend):
    st.markdown(f"### {trend.get('hashtag', '#Unknown')} — **{trend.get('predicted_trend', '')}**")
    if trend.get("platform"):
        st.markdown(f"**Platform:** {trend['platform']}")
    if trend.get("likely_platforms"):
        st.markdown(f"**Platforms:** {', '.join(trend['likely_platforms'])}")
    st.write(f"**Score:** {trend.get('score', trend.get('combined_score', 0)):.3f}")
    st.write(f"**Predicted Engagement (Next 24h):** ~{trend.get('predicted_engagement_next_24h', 0):,}")

    st.markdown("**Top sample posts:**")
    for post in trend.get("top_posts", [])[:3]:
        url = post.get("url")
        eng = post.get("engagement", 0)
        if url:
            st.write(f"- [{url}]({url}) — ❤️ {eng:,}")
    st.markdown("---")

def refresh_predictions():
    with st.spinner("🔄 Running predictions... please wait"):
        subprocess.run(["python", "predictions.py"], check=True)
    st.success("✅ Predictions updated successfully!")

# =========================
# UI LAYOUT
# =========================
st.title("📊 AI-Powered Social Media Trend Forecast Dashboard")
st.write("Predicts trending hashtags and topics across TikTok, Instagram, and Facebook — next 24 hours.")

st.sidebar.header("⚙️ Options")
selected_platform = st.sidebar.selectbox("Choose platform:", PLATFORMS)
refresh = st.sidebar.button("🔁 Refresh Predictions")

if refresh:
    refresh_predictions()

# =========================
# MAIN DISPLAY
# =========================
file_path = get_file_for_platform(selected_platform)
data = load_json(file_path)

if not data:
    st.warning(f"No data found for {selected_platform}. Try clicking 'Refresh Predictions' to generate trends.")
else:
    st.success(f"✅ Showing top {len(data)} predicted trends for {selected_platform}")

    for i, trend in enumerate(data, 1):
        with st.container():
            st.markdown(f"## 🔹 #{i} {trend.get('hashtag', '')}")
            render_trend_card(trend)

# =========================
# FOOTER
# =========================
st.markdown("---")
st.markdown(
    f"<small>Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Built with ❤️ by Maira’s AI Analytics System</small>",
    unsafe_allow_html=True,
)

