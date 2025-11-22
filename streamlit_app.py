import streamlit as st
import pandas as pd
from transformers import pipeline
import plotly.express as px
import time
from datetime import datetime

st.set_page_config(page_title="Complaint Pro", layout="wide")
st.title("End-to-End Customer Complaint Analysis & Monitoring System")

# Load models
@st.cache_resource
def load_models():
    st.write("Waking up AI models... (first time ~40 sec)")
    sentiment = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment-latest")
    zero_shot = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
    return sentiment, zero_shot

sentiment_pipe, zero_shot_pipe = load_models()

# BULLETPROOF SENTIMENT MAPPING — HANDLES ALL POSSIBLE OUTPUTS
def get_sentiment_label(raw_label):
    label = str(raw_label).lower()
    if "neg" in label or "0" in label:
        return "NEGATIVE"
    elif "pos" in label or "2" in label:
        return "POSITIVE"
    else:
        return "NEUTRAL"

# SMART CATEGORY — fixes "Rechnung" → billing
def smart_category(text):
    text = text.lower()
    if any(x in text for x in ["rechnung", "geld", "abbuchung", "rückerstattung", "zahlung", "kosten"]):
        return "billing"
    if any(x in text for x in ["lieferung", "paket", "versand", "dhl", "zustellung"]):
        return "service"
    if any(x in text for x in ["defekt", "kaputt", "funktioniert nicht"]):
        return "product"
    if any(x in text for x in ["konto", "login", "passwort", "anmeldung", "gesperrt"]):
        return "account"
    return "support"

# Real German complaints
complaints = [
    "Rechnung kam doppelt – Geld abgebucht!",
    "Produkt defekt, Display flackert",
    "Lieferung 10 Tage verspätet – kein Tracking",
    "Kundenservice antwortet nicht mehr",
    "Konto gesperrt ohne Grund",
    "Super schnelle Lieferung – top!",
    "Login geht seit Update nicht",
    "Wurde doppelt abgebucht – Rückerstattung?",
    "Paket als zugestellt markiert aber nicht da",
    "Sehr zufrieden – gerne wieder!"
]

# State
if "done" not in st.session_state:
    st.session_state.done = False
    st.session_state.pos = st.session_state.neg = st.session_state.neu = 0
    st.session_state.cat_count = {"billing":0, "support":0, "product":0, "service":0, "account":0}
    st.session_state.neg_words = []

live = st.empty()
charts = st.empty()
wc = st.empty()
final = st.container()

i = 0
while i < 20:
    text = complaints[i % len(complaints)]
    
    # REAL SENTIMENT
    raw_result = sentiment_pipe(text)[0]
    raw_label = raw_result["label"]  # e.g., "negative", "LABEL_0", "NEGATIVE"
    sentiment = get_sentiment_label(raw_label)
    
    if sentiment == "NEGATIVE":
        st.session_state.neg += 1
        st.session_state.neg_words.append(text)
    elif sentiment == "POSITIVE":
        st.session_state.pos += 1
    else:
        st.session_state.neu += 1
    
    # SMART CATEGORY
    category = smart_category(text)
    st.session_state.cat_count[category] += 1

    # LIVE UPDATE
    with live.container():
        st.success(f"{i+1}/20 → {category.upper()} | {sentiment} | {text[:70]}...")

    with charts.container():
        col1, col2 = st.columns(2)
        with col1:
            fig_bar = px.bar(x=list(st.session_state.cat_count.keys()), 
                           y=list(st.session_state.cat_count.values()),
                           color_discrete_sequence=["#636EFA"])
            st.plotly_chart(fig_bar, use_container_width=True)
        with col2:
            fig_pie = px.pie(values=[st.session_state.pos, st.session_state.neg, st.session_state.neu],
                           names=["POSITIVE","NEGATIVE","NEUTRAL"],
                           color_discrete_sequence=["#00CC96","#FF4444","#636EFA"])
            st.plotly_chart(fig_pie, use_container_width=True)

    # Negative word cloud
    if len(st.session_state.neg_words) > 2:
        from wordcloud import WordCloud
        import matplotlib.pyplot as plt
        cloud = WordCloud(width=600, height=300, background_color="black", colormap="Reds")\
                .generate(" ".join(st.session_state.neg_words))
        fig, ax = plt.subplots()
        ax.imshow(cloud); ax.axis("off")
        wc.pyplot(fig)

    i += 1
    time.sleep(2.3)

# FINAL
with final.container():
    st.balloons()
    st.success("20 COMPLAINTS ANALYZED!")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total", 20)
    col2.metric("Positive", st.session_state.pos)
    col3.metric("Negative", st.session_state.neg)

    st.subheader("FINAL CATEGORIES")
    st.plotly_chart(px.bar(x=list(st.session_state.cat_count.keys()), y=list(st.session_state.cat_count.values())))

    st.subheader("FINAL SENTIMENT")
    st.plotly_chart(px.pie(values=[st.session_state.pos, st.session_state.neg, st.session_state.neu],
                           names=["POSITIVE","NEGATIVE","NEUTRAL"],
                           color_discrete_sequence=["#00CC96","#FF4444","#636EFA"]))

    st.caption("100% FIXED: neg/NEG/LABEL_0 → NEGATIVE | Rechnung → billing • Jay Khakhar")
