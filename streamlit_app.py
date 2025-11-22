import streamlit as st
import requests
import time
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# ------------------- PAGE CONFIG -------------------
st.set_page_config(page_title="LIVE", layout="wide")
st.title("COMPLAINTS FLYING IN — SENTIMENT FIXED ⚡")

# ------------------- UI PLACEHOLDERS -------------------
live = st.empty()
charts = st.empty()
wc = st.empty()
final = st.empty()

# ------------------- STATE -------------------
sentiment_counts = {"pos":0, "neg":0, "neu":0}
category_counts = {"billing":0, "support":0, "product":0, "service":0, "account":0}
negative_words = []

# ------------------- LOAD DATA -------------------
df = pd.read_parquet("complaintpro/data/processed/complaints.parquet").sample(20)

# ------------------- SENTIMENT NORMALIZATION -------------------
def normalize_sent(s):
    s = s.lower()
    if "neg" in s:
        return "neg"
    elif "pos" in s:
        return "pos"
    return "neu"

# ------------------- LOOP -------------------
for i, text in enumerate(df["clean_text"]):
    try:
        response = requests.post("http://localhost:8000/predict", json={"text": text})
        data = response.json()

        # Update live log
        live.success(f"{i+1}/20 → {data['category'].upper()} | {data['sentiment']} | {data['text']}...")

        # Category count
        cat = data["category"]
        if cat in category_counts:
            category_counts[cat] += 1

        # Sentiment count
        s = normalize_sent(data["sentiment"])
        sentiment_counts[s] += 1

        if s == "neg":
            negative_words.append(data["text"])

        # ------------------- UPDATE CHARTS -------------------
        with charts.container():
            c1, c2 = st.columns(2)

            # Category chart
            c1.plotly_chart(
                px.bar(
                    x=list(category_counts.keys()),
                    y=list(category_counts.values()),
                    title="Live Categories"
                ),
                use_container_width=True
            )

            # Sentiment pie
            c2.plotly_chart(
                px.pie(
                    names=["Positive", "Negative", "Neutral"],
                    values=[
                        sentiment_counts["pos"],
                        sentiment_counts["neg"],
                        sentiment_counts["neu"],
                    ],
                    title="Live Sentiment",
                    color_discrete_sequence=["#00CC96", "#FF4444", "#636EFA"]
                ),
                use_container_width=True
            )

        # ------------------- WORD CLOUD -------------------
        if len(negative_words) > 2:
            cloud = WordCloud(
                width=400, height=300, background_color="black", colormap="Reds"
            ).generate(" ".join(negative_words))

            fig, ax = plt.subplots()
            ax.imshow(cloud)
            ax.axis("off")
            wc.pyplot(fig)

        time.sleep(1.5)

    except Exception as e:
        print("Error:", e)
        time.sleep(1)

# ------------------- FINAL SUMMARY -------------------
with final.container():
    st.balloons()
    st.success("20 COMPLAINTS ANALYZED!")

    total = sum(sentiment_counts.values())

    c1, c2, c3 = st.columns(3)
    c1.metric("Total", total)
    c2.metric("Positive", sentiment_counts["pos"])
    c3.metric("Negative", sentiment_counts["neg"])

    st.subheader("FINAL CATEGORIES")
    st.plotly_chart(
        px.bar(x=list(category_counts.keys()), y=list(category_counts.values()))
    )

    st.subheader("FINAL SENTIMENT")
    st.plotly_chart(
        px.pie(
            names=["Positive", "Negative", "Neutral"],
            values=[
                sentiment_counts["pos"],
                sentiment_counts["neg"],
                sentiment_counts["neu"],
            ],
            color_discrete_sequence=["#00CC96", "#FF4444", "#636EFA"]
        )
    )
