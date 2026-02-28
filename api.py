from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import json
from collections import defaultdict
from datetime import datetime

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Allow local development flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

active_connections = []

# ================= ANALYTICS STATE ================= #

analytics = {
    "total_requests": 0,
    "total_sanitized": 0,
    "total_restored": 0,
    "type_counts": defaultdict(int),
    "provider_counts": defaultdict(int),
    "daily_counts": defaultdict(int),
    "risk_total": 0
}


# ================= DASHBOARD ROUTE ================= #

@app.get("/")
async def get_dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


# ================= WEBSOCKET ================= #

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)

    # Send initial state when dashboard connects
    await websocket.send_text(json.dumps(build_dashboard_payload()))

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)


# ================= EVENT INGEST ================= #

@app.post("/event")
async def receive_event(data: dict):

    event_type = data.get("event_type")

    if event_type == "REQUEST_SEEN":
        analytics["total_requests"] += 1

    elif event_type == "SANITIZED_REQUEST":
        analytics["total_sanitized"] += 1

        # Daily count
        timestamp = data.get("timestamp")
        if timestamp:
            try:
                date_key = datetime.fromisoformat(timestamp).date().isoformat()
                analytics["daily_counts"][date_key] += 1
            except:
                pass

        # Type distribution
        types_detected = data.get("types_detected", {})
        for t, count in types_detected.items():
            analytics["type_counts"][t] += count

        # Provider tracking
        provider = data.get("provider")
        if provider:
            analytics["provider_counts"][provider] += 1

        # Risk aggregation
        risk = data.get("risk_score", 0)
        analytics["risk_total"] += risk

    elif event_type == "RESTORED_RESPONSE":
        analytics["total_restored"] += 1

    # Broadcast updated dashboard state
    payload = build_dashboard_payload()
    await broadcast(payload)

    return {"status": "ok"}


# ================= DASHBOARD PAYLOAD BUILDER ================= #

def build_dashboard_payload():

    protection_rate = 0
    if analytics["total_requests"] > 0:
        protection_rate = (
            analytics["total_sanitized"] / analytics["total_requests"]
        ) * 100

    return {
        "summary": {
            "total_requests": analytics["total_requests"],
            "total_sanitized": analytics["total_sanitized"],
            "total_restored": analytics["total_restored"],
            "protection_rate": round(protection_rate, 2),
            "average_risk_score": (
                round(analytics["risk_total"] / analytics["total_sanitized"], 2)
                if analytics["total_sanitized"] > 0 else 0
            )
        },
        "daily_counts": analytics["daily_counts"],
        "type_distribution": analytics["type_counts"],
        "provider_distribution": analytics["provider_counts"]
    }


# ================= BROADCAST ================= #

async def broadcast(payload):

    disconnected = []

    for connection in active_connections:
        try:
            await connection.send_text(json.dumps(payload))
        except:
            disconnected.append(connection)

    for dc in disconnected:
        if dc in active_connections:
            active_connections.remove(dc)
