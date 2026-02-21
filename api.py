from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import json

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


# ================= DASHBOARD ROUTE ================= #

@app.get("/")
async def get_dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


# ================= WEBSOCKET ================= #

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)


# ================= EVENT INGEST ================= #

@app.post("/event")
async def receive_event(data: dict):

    disconnected_clients = []

    for connection in active_connections:
        try:
            await connection.send_text(json.dumps(data))
        except:
            disconnected_clients.append(connection)

    # Clean up dead connections
    for dc in disconnected_clients:
        if dc in active_connections:
            active_connections.remove(dc)

    return {"status": "ok"}