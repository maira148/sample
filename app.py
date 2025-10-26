import streamlit as st
import json
import os
import subprocess
from datetime import datetime

# =========================
# CONFIGURATION
# =========================
st.set_page_config(
    page_title="Social Media Trend Forecast",
    layout="wide",
    page_icon="📊",
)

# Dynamically detect predictions folder or fallback to root
if os.path.isdir("predictions"):
    DATA_DIR = "predictions"
else:
    DATA_DIR = "."

PLATFORMS = ["Instagram", "TikTok", "Facebook", "Combined"]

# =========================
# HELPERS
# =========================
def load_json(file_path):
    """Safely load JSON data from file."""
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading {file_path}: {e}")
        return []

def get_file_for_platform(platform):
    """Return filename for each platform."""
    mapping = {
        "Instagram": "instagram_trends.json",
        "TikTok": "tiktok_trends.json",
        "Facebook": "facebook_trends.json",
        "Combined": "combined_trends.json",
    }
    return os.path.join(DATA_DIR, mapping[platform])

def render_trend_card(trend):
    """Render a single trend as a styled card."""
    st.markdown(f"### {trend.get('hashtag', '#Unknown')} — **{trend.get('predicted_trend', '')}**")
    if trend.get("platform"):
        st.markdown(f"**Platform:** {trend['platform']}")
    if trend.get("likely_platforms"):
        st.markdown(f"**Platforms:** {', '.join(trend['likely_platforms'])}")
    st.write(f"**Score:** {trend.get('score', trend.get('combined_score', 0)):.3f}")
    st.write(f"**Predicted Engagement (Next 24h):** ~{trend.get('predicted_engagement_next_24h', 0):,}")

    if trend.get("top_posts"):
        st.markdown("**Top sample posts:**")
        for post in trend.get("top_posts", [])[:3]:
            url = post.get("url")
            eng = post.get("engagement", 0)
            if url:
                st.write(f"- [{url}]({url}) — ❤️ {eng:,}")
    st.markdown("---")

def refresh_predictions():
    """Re-run predictions.py when user requests a refresh."""
    with st.spinner("🔄 Running predictions... please wait"):
        try:
            subprocess.run(["python", "predictions.py"], check=True)
            st.success("✅ Predictions updated successfully!")
        except Exception as e:
            st.error(f"Failed to run predictions.py: {e}")

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
    st.warning(f"No data found for {selected_platform}. Upload trend JSONs or click 'Refresh Predictions'.")
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
