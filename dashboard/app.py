import streamlit as st
import requests
import time
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt

st.set_page_config(page_title="ComplaintPro", layout="wide")
st.title("COMPLAINTS FLYING IN — LIVE DEMO")

# 3 COLUMNS
left, mid, right = st.columns([2, 2, 1])

live = left.empty()
chart = mid.empty()
wc = right.empty()

# DATA
complaints = []
neg_words = []
cats = {"billing":0, "support":0, "product":0, "service":0, "account":0}
senti = {"POS":0, "NEG":0}

# API URL (YOUR LIVE NGROK)
API = "https://mediately-screwlike-earleen.ngrok-free.dev/predict"

# SEND 20 COMPLAINTS
import pandas as pd
df = pd.read_parquet("complaintpro/data/processed/complaints.parquet").sample(20)
for i, txt in enumerate(df["clean_text"]):
    try:
        r = requests.post(API, json={"text": txt})
        data = r.json()
        
        # SAVE
        complaints.append(data)
        if "NEG" in data['sentiment']:
            neg_words.append(data['text'])
        cats[data['category']] += 1
        senti[data['sentiment']] += 1
        
        # LIVE TEXT
        live.success(f"{data['category'].upper()} | {data['sentiment']} | {data['text'][:80]}...")
        
        # BAR + PIE
        fig1 = px.bar(x=list(cats.keys()), y=list(cats.values()), title="Categories")
        fig2 = px.pie(values=list(senti.values()), names=list(senti.keys()), title="Sentiment")
        chart.plotly_chart(fig1, use_container_width=True)
        chart.plotly_chart(fig2, use_container_width=True)
        
        # WORD CLOUD
        if len(neg_words) > 2:
            cloud = WordCloud(width=300, height=300, background_color='black', colormap='Oranges').generate(" ".join(neg_words))
            fig, ax = plt.subplots()
            ax.imshow(cloud); ax.axis("off")
            wc.pyplot(fig)
        
        time.sleep(1.5)
    except:
        time.sleep(1)

# FINAL
st.balloons()
st.success(f"20 COMPLAINTS ANALYZED!")
st.metric("Total", len(complaints))
st.metric("Negative", senti["NEG"])
st.plotly_chart(px.bar(x=list(cats.keys()), y=list(cats.values()), title="FINAL CATEGORIES"))