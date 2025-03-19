from fastapi import WebSocket
from typing import List, Dict, Tuple

class ConnectionManager:
    def __init__(self):
        # Kluczem jest nazwa pokoju, a wartością lista krotek (websocket, nickname)
        self.active_connections: Dict[str, List[Tuple[WebSocket, str]]] = {}

    async def connect(self, room: str, websocket: WebSocket, nickname: str):
        await websocket.accept()
        if room not in self.active_connections:
            self.active_connections[room] = []
        self.active_connections[room].append((websocket, nickname))

    def disconnect(self, room: str, websocket: WebSocket):
        if room in self.active_connections:
            self.active_connections[room] = [
                (ws, nick) for ws, nick in self.active_connections[room] if ws != websocket
            ]

    async def broadcast(self, room: str, data: dict):
        if room in self.active_connections:
            for connection, _ in self.active_connections[room]:
                await connection.send_json(data)
