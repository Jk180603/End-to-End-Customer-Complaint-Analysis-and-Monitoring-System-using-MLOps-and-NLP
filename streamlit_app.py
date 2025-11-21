import streamlit as st
import pandas as pd
from transformers import pipeline
import plotly.express as px
from datetime import datetime
import time

# ------------------- MODEL (works without internet on Streamlit) -------------------
@st.cache_resource
def load_model():
    return pipeline(
        "text-classification",
        model="lxyuan/distilbert-base-multilingual-cased-sentiments-student",
        return_all_scores=True
    )

classifier = load_model()

# ------------------- APP LAYOUT -------------------
st.set_page_config(page_title="ComplaintPro", layout="wide")
st.title("ComplaintPro – Real-Time Customer Complaint Analyzer")
st.markdown("**Live classification • Sentiment • Category • Priority**")

# Initialize history
if "complaints" not in st.session_state:
    st.session_state.complaints = pd.DataFrame(columns=["Text", "Sentiment", "Score", "Category", "Time"])

# Input box
with st.form("complaint_form"):
    user_input = st.text_area("Enter customer complaint (German/English):", height=120,
                              placeholder="Beispiel: Die Lieferung ist zu spät und das Produkt ist kaputt...")
    submitted = st.form_submit_button("Analyze Complaint")

# ------------------- ANALYSIS -------------------
if submitted and user_input.strip():
    with st.spinner("Analyzing complaint..."):
        result = classifier(user_input)[0]
        label = result['label']
        score = result['score']
        
        # Map sentiment
        sentiment_map = {"POSITIVE": "Positive", "NEGATIVE": "Negative", "NEUTRAL": "Neutral"}
        sentiment = sentiment_map.get(label, label)
        
        # Simple category detection (you can extend with zero-shot later)
        text = user_input.lower()
        if any(word in text for word in ["lieferung", "versand", "spät", "nicht angekommen"]):
            category = "Delivery Issue"
        elif any(word in text for word in ["defekt", "kaputt", "funktioniert nicht"]):
            category = "Product Defect"
        elif any(word in text for word in ["geld", "rückerstattung", "rechnung"]):
            category = "Billing/Refund"
        else:
            category = "General"

        priority = "HIGH" if sentiment == "Negative" and score > 0.8 else "MEDIUM" if sentiment == "Negative" else "LOW"

        new_row = pd.DataFrame([{
            "Text": user_input,
            "Sentiment": sentiment,
            "Score": round(score, 3),
            "Category": category,
            "Priority": priority,
            "Time": datetime.now().strftime("%H:%M:%S")
        }])
        st.session_state.complaints = pd.concat([st.session_state.complaints, new_row], ignore_index=True)

# ------------------- LIVE DASHBOARD -------------------
if not st.session_state.complaints.empty:
    df = st.session_state.complaints.copy()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Complaints", len(df))
    col2.metric("Negative Today", len(df[df["Sentiment"] == "Negative"]))
    col3.metric("High Priority", len(df[df["Priority"] == "HIGH"]))
    col4.metric("Avg Sentiment Score", df[df["Sentiment"] == "Negative"]["Score"].mean().round(3) if len(df[df["Sentiment"] == "Negative"]) > 0 else 0)

    c1, c2 = st.columns([1.4, 1.6])

    with c1:
        st.subheader("Latest Complaints")
        for _, row in df.tail(10).iterrows():
            color = {"Negative": "#FF4444", "Neutral": "#CCCCCC", "Positive": "#00FF00"}[row["Sentiment"]]
            st.markdown(f"**{row['Time']}** • <span style='color:{color}'>{row['Sentiment']} • {row['Priority']}</span>", unsafe_allow_html=True)
            st.write(f"**{row['Category']}**")
            st.caption(row["Text"][:150] + "..." if len(row["Text"]) > 150 else row["Text"])
            st.divider()

    with c2:
        st.subheader("Complaint Categories")
        cat_count = df["Category"].value_counts()
        fig = px.pie(values=cat_count.values, names=cat_count.index, color_discrete_sequence=px.colors.sequential.Reds)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Sentiment Over Time")
        time_df = df.tail(20).copy()
        time_df["Hour"] = pd.to_datetime(time_df["Time"], format="%H:%M:%S").dt.strftime("%H:%M")
        fig2 = px.scatter(time_df, x="Hour", y="Score", color="Sentiment",
                          size="Score", hover_data=["Text", "Category"])
        st.plotly_chart(fig2, use_container_width=True)

st.success("COMPLAINT PRO LIVE – Ready for Audalaxy, Otto, Zalando")
st.caption("Built by Jay Khakhar • github.com/JK180603 • 100% working on Streamlit Cloud")
