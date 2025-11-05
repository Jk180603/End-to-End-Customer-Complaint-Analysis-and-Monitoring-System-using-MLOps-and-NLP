from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from transformers import pipeline
import asyncio

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"])

sentiment = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment-latest")
zero_shot = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
cats = ["billing", "service", "support", "product", "account"]

clients = []

@app.websocket("/ws")
async def ws(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    try:
        while True: await asyncio.sleep(1)
    except: clients.remove(websocket)

@app.post("/predict")
async def predict(data: dict):
    text = data.get("text", "")
    s = sentiment(text)[0]
    c = zero_shot(text, candidate_labels=cats)[0]
    result = {
        "text": text[:90] + "...",
        "sentiment": s["label"][:3],
        "score": round(s["score"], 2),
        "category": c["labels"][0]
    }
    for c in clients[:]:
        try: await c.send_json(result)
        except: clients.remove(c)
    return result