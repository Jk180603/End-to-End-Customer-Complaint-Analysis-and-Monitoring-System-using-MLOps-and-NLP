import streamlit as st
import pandas as pd
from transformers import pipeline
import plotly.express as px
from datetime import datetime

# ------------------- MODEL -------------------
@st.cache_resource
def load_model():
    return pipeline(
        "text-classification",
        model="cardiffnlp/twitter-roberta-base-sentiment-latest",
        return_all_scores=True
    )

classifier = load_model()

# ------------------- CATEGORY & PRIORITY LOGIC -------------------
def classify_category(text):
    text = text.lower()
    if any(k in text for k in ["account", "login", "password", "konto", "anmeldung"]):
        return "Account"
    elif any(k in text for k in ["delivery", "lieferung", "versand", "spät", "nicht angekommen", "paket"]):
        return "Delivery"
    elif any(k in text for k in ["defekt", "kaputt", "broken", "funktioniert nicht", "produkt"]):
        return "Product Defect"
    elif any(k in text for k in ["billing", "rechnung", "geld", "refund", "rückerstattung", "zahlung"]):
        return "Billing"
    else:
        return "Other"

def get_sentiment_and_priority(row):
    result = classifier(row["Text"])[0]
    scores = {x['label']: x['score'] for x in result}
    sentiment = max(scores, key=scores.get)  # LABEL_POS, LABEL_NEU, LABEL_NEG
    score = scores[sentiment]
    
    if sentiment == "LABEL_NEG" and score > 0.8:
        priority = "High"
    elif sentiment == "LABEL_NEG":
        priority = "Medium"
    else:
        priority = "Low"
        
    return sentiment.replace("LABEL_", ""), round(score, 3), priority

# ------------------- APP -------------------
st.set_page_config(page_title="ComplaintPro", layout="wide")
st.title("ComplaintPro – Live Customer Complaint Analytics")
st.markdown("**Upload CSV → Auto-classify → Real-time Dashboard**")

# File uploader
uploaded_file = st.file_uploader("Upload your complaints CSV (columns: 'Text')", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    
    if "Text" not in df.columns:
        st.error("CSV must have a column named 'Text'")
        st.stop()
    
    with st.spinner("Classifying all complaints..."):
        df["Category"] = df["Text"].apply(classify_category)
        results = df["Text"].apply(get_sentiment_and_priority)
        df[["Sentiment", "Confidence", "Priority"]] = pd.DataFrame(results.tolist(), index=df.index)
        df["Time"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    st.success(f"Successfully analyzed {len(df)} complaints!")

    # Dashboard
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Complaints", len(df))
    col2.metric("Negative", len(df[df["Sentiment"] == "NEG"]))
    col3.metric("High Priority", len(df[df["Priority"] == "High"]))
    col4.metric("Most Common", df["Category"].mode()[0] if not df["Category"].empty else "-")

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Complaints by Category")
        fig1 = px.bar(df["Category"].value_counts(), color=df["Category"].value_counts().index)
        st.plotly_chart(fig1, use_container_width=True)

        st.subheader("Sentiment Distribution")
        fig2 = px.pie(values=df["Sentiment"].value_counts().values,
                      names=df["Sentiment"].value_counts().index,
                      color_discrete_sequence=["#FF4444", "#FFD700", "#44FF44"])
        st.plotly_chart(fig2, use_container_width=True)

    with c2:
        st.subheader("Priority Heatmap")
        priority_df = df.groupby(["Category", "Priority"]).size().unstack(fill_value=0)
        fig3 = px.imshow(priority_df.values,
                         labels=dict(x="Priority", y="Category", color="Count"),
                         x=priority_df.columns, y=priority_df.index,
                         color_continuous_scale="Reds")
        st.plotly_chart(fig3, use_container_width=True)

        st.subheader("Latest 10 Complaints")
        st.dataframe(df[["Text", "Category", "Sentiment", "Priority", "Confidence"]].head(10))

    st.download_button("Download Results", df.to_csv(index=False).encode(), "complaints_analyzed.csv")

else:
    st.info("Upload a CSV with customer complaints to start analysis")
    st.caption("Example column: 'Text' → 'Mein Konto funktioniert nicht und die Lieferung ist verspätet'")
