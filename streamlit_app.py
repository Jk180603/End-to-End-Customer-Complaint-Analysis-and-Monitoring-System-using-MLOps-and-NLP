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
    st.write("Loading AI models... (first time ~40 sec)")
    sentiment = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment-latest")
    zero_shot = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
    return sentiment, zero_shot

sentiment_pipe, zero_shot_pipe = load_models()

# BETTER CATEGORY KEYWORDS — fixes "Rechnung" → billing issue
category_keywords = {
    "billing": ["rechnung", "geld", "abbuchung", "rückerstattung", "zahlung", "bezahlt", "kosten"],
    "support": ["kundenservice", "hilfe", "warteschleife", "antwortet nicht", "telefon"],
    "product": ["defekt", "kaputt", "funktioniert nicht", "qualität", "beschädigt"],
    "service": ["lieferung", "versand", "paket", "dhl", "zustellung", "tracking"],
    "account": ["konto", "login", "passwort", "anmeldung", "gesperrt"]
}

def smart_category(text):
    text = text.lower()
    scores = {}
    for cat, words in category_keywords.items():
        scores[cat] = sum(1 for w in words if w in text)
    return max(scores, key=scores.get) if max(scores.values()) > 0 else "support"

# Real German complaints
complaints = [
    "Rechnung kam doppelt – Geld trotzdem abgebucht!",
    "Produkt defekt angekommen, Umtausch abgelehnt",
    "Lieferung 10 Tage verspätet – kein Tracking",
    "Kundenservice antwortet seit Wochen nicht",
    "Konto gesperrt obwohl alles bezahlt",
    "Super schnelle Lieferung – top Service!",
    "Login funktioniert seit Update nicht mehr",
    "Wurde doppelt abgebucht – bitte Rückerstattung",
    "Paket als zugestellt markiert aber nicht da",
    "Sehr zufrieden – gerne wieder!"
]

# State
if "done" not in st.session_state:
    st.session_state.done = False
    st.session_state.pos = st.session_state.neg = st.session_state.neu = 0
    st.session_state.cat_count = {c:0 for c in category_keywords}
    st.session_state.neg_words = []

live = st.empty()
charts = st.empty()
wc = st.empty()
final = st.container()

i = 0
while i < 20:
    text = complaints[i % len(complaints)]
    
    # Real sentiment
    raw = sentiment_pipe(text)[0]["label"].lower()
    if "neg" in raw:
        sentiment = "NEGATIVE"
        st.session_state.neg += 1
        st.session_state.neg_words.append(text)
    elif "pos" in raw:
        sentiment = "POSITIVE"
        st.session_state.pos += 1
    else:
        sentiment = "NEUTRAL"
        st.session_state.neu += 1
    
    # SMART CATEGORY — now "Rechnung" correctly goes to billing
    category = smart_category(text)
    st.session_state.cat_count[category] += 1

    # Live update
    with live.container():
        st.success(f"{i+1}/20 → {category.upper()} | {sentiment} | {text[:75]}...")

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

    if len(st.session_state.neg_words) > 2:
        from wordcloud import WordCloud
        import matplotlib.pyplot as plt
        cloud = WordCloud(width=600, height=300, background_color="black", colormap="Reds")\
                .generate(" ".join(st.session_state.neg_words))
        fig, ax = plt.subplots()
        ax.imshow(cloud); ax.axis("off")
        wc.pyplot(fig)

    i += 1
    time.sleep(2.2)

# FINAL RESULT
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

    st.caption("Fixed: Rechnung → billing | neg/NEG → NEGATIVE | Live HF models • Jay Khakhar")
