import streamlit as st
import pandas as pd
from pytrends.request import TrendReq
import requests
import praw
import os  # for environment variables

# --- Hugging Face API ---
HUGGINGFACE_API = "https://api-inference.huggingface.co/models/facebook/blenderbot-400M-distill"
HUGGINGFACE_KEY = os.environ.get("HUGGINGFACE_KEY")  # set in Streamlit secrets or local env
HEADERS = {"Authorization": f"Bearer {HUGGINGFACE_KEY}"} if HUGGINGFACE_KEY else {}

# --- Reddit API ---
CLIENT_ID = os.environ.get("REDDIT_CLIENT_ID")        # from environment variable
CLIENT_SECRET = os.environ.get("REDDIT_CLIENT_SECRET")
USER_AGENT = os.environ.get("REDDIT_USER_AGENT", "MyContentApp/0.1 by u/username")

reddit = praw.Reddit(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    user_agent=USER_AGENT
)

# --- Functions ---
def get_google_trends(keyword, region='IN'):
    pytrends = TrendReq()
    pytrends.build_payload([keyword], timeframe='today 12-m', geo=region)
    df = pytrends.interest_over_time()
    return df

def get_reddit_posts_by_search(topic, limit=5):
    try:
        posts = []
        for submission in reddit.subreddit("all").search(topic, sort="hot", limit=limit):
            posts.append({"title": submission.title, "score": submission.score, "url": submission.url})
        if not posts:
            return pd.DataFrame([{"title": f"No live posts found for '{topic}'", "score": 0, "url": ""}])
        return pd.DataFrame(posts)
    except Exception as e:
        return pd.DataFrame([{"title": f"Error fetching posts: {e}", "score": 0, "url": ""}])

def generate_content_ideas(topic, audience):
    if not HUGGINGFACE_KEY:
        return [
            f"Top 5 {topic} hacks {audience} swears by",
            f"Myth-busting {topic} routine for {audience}",
            f"30-day challenge: Smarter {topic} tips"
        ]
    try:
        prompt = f"Write 3 creative and catchy blog titles about '{topic}' for {audience}, relevant to current trends."
        response = requests.post(HUGGINGFACE_API, headers=HEADERS, json={"inputs": prompt}, timeout=20)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and "generated_text" in data[0]:
                text = data[0]["generated_text"]
                titles = [t.strip() for t in text.replace("\n", ". ").split(".") if t.strip()]
                return titles[:3]
    except Exception as e:
        print("Hugging Face error:", e)
    return [
        f"Top 5 {topic} hacks {audience} swears by",
        f"Myth-busting {topic} routine for {audience}",
        f"30-day challenge: Smarter {topic} tips"
    ]

def generate_content_calendar(topic, audience):
    return f"""30-Day Content Calendar
Week 1:
- Day 1: Reel - "{topic} Hacks"
- Day 3: Blog - "{topic} Routine Review"
- Day 5: Short - "Night Routine in 30s"
... (repeat for 30 days)
"""

# ---- Streamlit UI ----
st.title("ðŸ§­ AI Content Strategy Engine")

topic = st.text_input("Enter topic:", "movies")
audience = st.text_input("Enter target audience:", "Gen Z")

if st.button("Run Strategy Engine"):
    st.subheader("ðŸ“ˆ Google Trends")
    df = get_google_trends(topic)
    if not df.empty:
        st.line_chart(df[topic])

    st.subheader("ðŸ“¢ Reddit Buzz")
    reddit_posts = get_reddit_posts_by_search(topic, limit=5)
    # Make posts clickable
    for index, row in reddit_posts.iterrows():
        st.markdown(f"- [{row['title']}]({row['url']}) â€” Score: {row['score']}")

    st.subheader("ðŸ’¡ AI Content Ideas")
    ideas = generate_content_ideas(topic, audience)
    for i, idea in enumerate(ideas, 1):
        st.write(f"{i}. {idea}")

    st.subheader("ðŸ—“ï¸ AI 30-Day Calendar")
    st.text(generate_content_calendar(topic, audience))
