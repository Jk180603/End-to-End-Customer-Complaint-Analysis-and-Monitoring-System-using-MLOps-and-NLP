import streamlit as st
import requests
from transformers import pipeline

st.title("Live Complaint Classifier")

# --- Load sentiment model ---
sentiment_model = pipeline("sentiment-analysis")

# Categories (fallback)
CATEGORIES = ["delivery", "product", "service", "payment", "refund"]

# Fake classifier for category (only temporary)
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
model = AutoModelForSequenceClassification.from_pretrained(
    "distilbert-base-uncased",
    num_labels=len(CATEGORIES)
)

def classify_category(text):
    """Temporary text classification to distinguish categories"""
    inputs = tokenizer(text, return_tensors="pt", truncation=True)
    logits = model(**inputs).logits
    pred = torch.argmax(logits, dim=1).item()
    return CATEGORIES[pred]

# -------------------------------------------------------------------
# 🔥 FETCH DATA FROM API + DEBUG LOGGING (MOST IMPORTANT PART)
# -------------------------------------------------------------------
API_URL = "http://127.0.0.1:8000/get-complaints"  # your API URL

def fetch_api_data():
    try:
        response = requests.get(API_URL)

        # parse response
        data = response.json()

        # 🔥 DEBUG PRINTS — THIS WILL SOLVE THE ISSUE 🔥
        print("\n\n========= RAW API RESPONSE =========")
        print(data)
        print("====================================\n")

        st.write("DEBUG API RESPONSE:", data)

        return data
    except Exception as e:
        st.error(f"Error fetching API data: {e}")
        return []
# -------------------------------------------------------------------


# -------------------------------------------------------------------
# 🔥 PROCESS EACH COMPLAINT
# -------------------------------------------------------------------
def process_complaints(data):
    processed_list = []

    for item in data:

        # -----------------------------------------------
        # 1) Detect where the review text is actually stored
        # -----------------------------------------------
        text = None

        POSSIBLE_KEYS = ["review", "message", "comment", "text", "body", "content"]

        for k in POSSIBLE_KEYS:
            if k in item and isinstance(item[k], str):
                text = item[k]
                break

        # if nothing found
        if not text:
            text = str(item)  # last fallback

        # -----------------------------------------------
        # 2) DEBUG: show extracted text
        # -----------------------------------------------
        print("\nExtracted Text:", text)
        st.write("Extracted Text:", text)

        # -----------------------------------------------
        # 3) SENTIMENT CLASSIFICATION
        # -----------------------------------------------
        sentiment = sentiment_model(text)[0]
        sentiment_label = sentiment['label']  # POSITIVE / NEGATIVE / NEUTRAL

        # -----------------------------------------------
        # 4) CATEGORY CLASSIFICATION
        # -----------------------------------------------
        category = classify_category(text)

        processed_list.append({
            "text": text,
            "sentiment": sentiment_label,
            "category": category
        })

    return processed_list


# -------------------------------------------------------------------
# 🔥 MAIN PROCESSING
# -------------------------------------------------------------------
data = fetch_api_data()

if data:
    result = process_complaints(data)

    st.subheader("Processed Complaints")
    st.write(result)
