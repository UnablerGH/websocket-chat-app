from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
from manager import ConnectionManager

app = FastAPI()

# Montujemy katalog ze statycznymi plikami (CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

manager = ConnectionManager()

@app.get("/", response_class=HTMLResponse)
async def get(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

@app.websocket("/ws/{room}/{nickname}")
async def websocket_endpoint(websocket: WebSocket, room: str, nickname: str):
    await manager.connect(room, websocket, nickname)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                data_json = json.loads(data)
            except Exception:
                continue

            if data_json.get("type") == "chat":
                await manager.broadcast(room, data_json)
            elif data_json.get("type") == "typing":
                await manager.broadcast(room, data_json)
            elif data_json.get("type") == "notification":
                await manager.broadcast(room, data_json)
            elif data_json.get("type") == "image":
                await manager.broadcast(room, data_json)
    except WebSocketDisconnect:
        manager.disconnect(room, websocket)
        notif = {
            "type": "notification",
            "message": f"{nickname} opuścił pokój {room}"
        }
        await manager.broadcast(room, notif)
