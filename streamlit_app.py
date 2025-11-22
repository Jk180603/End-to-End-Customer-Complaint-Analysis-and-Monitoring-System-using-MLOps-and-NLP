import streamlit as st
import pandas as pd
from transformers import pipeline
import time
from datetime import datetime
import random

st.set_page_config(page_title="Complaint Pro", layout="wide")
st.title("End-to-End Customer Complaint Analysis and Monitoring System")

# Load models once
@st.cache_resource
def load_models():
    sentiment = pipeline("sentiment-analysis", 
                         model="cardiffnlp/twitter-roberta-base-sentiment-latest")
    zero_shot = pipeline("zero-shot-classification", 
                         model="facebook/bart-large-mnli")
    return sentiment, zero_shot

sentiment_pipe, zero_shot_pipe = load_models()
categories = ["billing", "support", "product", "service", "account"]

# Real German complaint pool (your original style)
real_complaints = [
    "Mein Paket ist seit 10 Tagen weg – DHL sagt zugestellt",
    "Produkt defekt, Bildschirm flackert, Umtausch abgelehnt",
    "Wurde doppelt abgebucht – bitte sofort Rückerstattung!",
    "Kundenservice antwortet seit 2 Wochen nicht",
    "Konto gesperrt obwohl ich alles bezahlt habe",
    "Rechnung falsch – Artikel nie erhalten",
    "40 Minuten Warteschleife und dann aufgelegt",
    "Super schnelle Lieferung – alles perfekt!",
    "Login funktioniert nicht mehr seit Update",
    "Top Service – gerne wieder!"
]

if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame()
    st.session_state.processed = 0

placeholder = st.empty()
final = st.container()

while True:
    time.sleep(4)

    if st.session_state.processed < 20:
        text = random.choice(real_complaints)
        
        # Real classification like your Colab
        sent_result = sentiment_pipe(text)[0]
        raw_label = sent_result["label"].lower()
        if "neg" in raw_label:
            sentiment = "Negative"
        elif "pos" in raw_label:
            sentiment = "Positive"
        else:
            sentiment = "Neutral"
            
        category_result = zero_shot_pipe(text, categories)
        category = category_result["labels"][0]

        new_row = pd.DataFrame([{
            "time": datetime.now().strftime("%H:%M:%S"),
            "complaint": text,
            "category": category,
            "sentiment": sentiment
        }])

        st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
        st.session_state.processed += 1

    df = st.session_state.df.copy()

    with placeholder.container():
        total = len(df)
        pos = len(df[df["sentiment"] == "Positive"])
        neg = len(df[df["sentiment"] == "Negative"])
        neu = len(df[df["sentiment"] == "Neutral"])

        col1, col2, col3 = st.columns(3)
        col1.metric("Total", total)
        col2.metric("Positive", pos)
        col3.metric("Negative", neg)

        cat_count = df["category"].value_counts().to_dict()

        st.subheader("FINAL CATEGORIES")
        st.bar_chart(cat_count)

        st.subheader("FINAL SENTIMENT")
        import plotly.express as px
        fig = px.pie(values=[pos, neg, neu], 
                     names=["POSITIVE", "NEGATIVE", "NEUTRAL"],
                     color_discrete_sequence=["#00CC96", "#FF4444", "#636EFA"])
        st.plotly_chart(fig, use_container_width=True)

    if st.session_state.processed >= 20:
        with final.container():
            st.balloons()
            st.success("20 COMPLAINTS ANALYZED!")
            break

    time.sleep(1)
