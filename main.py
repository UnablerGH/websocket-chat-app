from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from typing import List, Dict, Tuple
from datetime import datetime
import json

app = FastAPI()

html = """
<!DOCTYPE html>
<html>
<head>
  <title>FastAPI WebSocket Chat</title>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <!-- Bootstrap CSS -->
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    .chat-container {
      max-width: 600px;
      margin: auto;
    }
    .message {
      padding: 10px;
      margin: 5px;
      border-radius: 10px;
      max-width: 70%;
      word-wrap: break-word;
    }
    .sent {
      background-color: #d1e7dd;
      margin-left: auto;
      text-align: right;
    }
    .received {
      background-color: #f8d7da;
      margin-right: auto;
      text-align: left;
    }
    .notification {
      text-align: center;
      color: gray;
      font-style: italic;
    }
  </style>
</head>
<body>
<div class="container chat-container mt-4">
  <h2>FastAPI WebSocket Chat</h2>
  <div id="login">
    <div class="mb-3">
      <input type="text" id="nickname" class="form-control" placeholder="Wprowadź pseudonim">
    </div>
    <div class="mb-3">
      <input type="text" id="room" class="form-control" placeholder="Nazwa pokoju">
    </div>
    <button id="connectBtn" class="btn btn-primary mb-3">Połącz</button>
  </div>
  
  <div id="chat" style="display:none;">
    <div id="chat-box" style="height:400px; overflow-y: scroll; border: 1px solid #ccc; padding: 10px;"></div>
    <div id="typingIndicator" class="mb-2"></div>
    <form id="messageForm">
      <div class="mb-3">
        <input type="text" id="messageInput" class="form-control" placeholder="Wpisz wiadomość">
      </div>
      <div class="mb-3">
        <input type="file" id="imageInput" class="form-control">
      </div>
      <button type="submit" class="btn btn-success">Wyślij</button>
    </form>
  </div>
</div>

<script>
  let ws;
  let nickname;
  let room;
  
  document.getElementById("connectBtn").onclick = function() {
    nickname = document.getElementById("nickname").value.trim();
    room = document.getElementById("room").value.trim();
    if(nickname === "" || room === "") {
      alert("Proszę wypełnić oba pola!");
      return;
    }
    // Łączymy się z odpowiednim pokojem i pseudonimem
    ws = new WebSocket(`ws://${location.host}/ws/${room}/${nickname}`);
    
    ws.onopen = function() {
      console.log("Połączono");
      // Po nawiązaniu połączenia wysyłamy powiadomienie o dołączeniu
      let joinMsg = {
        type: "notification",
        message: nickname + " dołączył do pokoju " + room
      }
      ws.send(JSON.stringify(joinMsg));
      document.getElementById("login").style.display = "none";
      document.getElementById("chat").style.display = "block";
    }
    
    ws.onmessage = function(event) {
      let data = JSON.parse(event.data);
      if(data.type === "typing") {
        document.getElementById("typingIndicator").innerText = data.nickname + " pisze...";
        setTimeout(() => {
          document.getElementById("typingIndicator").innerText = "";
        }, 1000);
      } else if(data.type === "chat") {
        addMessage(data, data.nickname === nickname);
      } else if(data.type === "notification") {
        addNotification(data.message);
      } else if(data.type === "image") {
        addImageMessage(data, data.nickname === nickname);
      }
    }
    
    ws.onclose = function() {
      addNotification("Rozłączono z serwerem");
    }
  }
  
  // Informacja, że użytkownik zaczyna pisać
  document.getElementById("messageInput").addEventListener("keydown", function() {
    let typingMsg = {
      type: "typing",
      nickname: nickname
    }
    ws.send(JSON.stringify(typingMsg));
  });
  
  document.getElementById("messageForm").onsubmit = function(event) {
    event.preventDefault();
    let message = document.getElementById("messageInput").value;
    let file = document.getElementById("imageInput").files[0];
    
    // Jeśli wybrano obrazek, odczytujemy go jako base64 i wysyłamy
    if(file) {
      let reader = new FileReader();
      reader.onload = function(e) {
        let imageData = e.target.result;
        let msgData = {
          type: "image",
          nickname: nickname,
          timestamp: new Date().toLocaleString(),
          data: imageData
        };
        ws.send(JSON.stringify(msgData));
        addImageMessage(msgData, true);
      }
      reader.readAsDataURL(file);
      document.getElementById("imageInput").value = "";
    }
    // Jeśli wpisano wiadomość tekstową
    if(message.trim() !== "") {
      let msgData = {
        type: "chat",
        nickname: nickname,
        timestamp: new Date().toLocaleString(),
        message: message
      }
      ws.send(JSON.stringify(msgData));
      addMessage(msgData, true);
      document.getElementById("messageInput").value = "";
    }
  }
  
  function addMessage(data, isSelf=false) {
    let chatBox = document.getElementById("chat-box");
    let msgDiv = document.createElement("div");
    msgDiv.classList.add("message");
    msgDiv.classList.add(isSelf ? "sent" : "received");
    msgDiv.innerHTML = `<strong>${data.nickname}</strong> <small>${data.timestamp}</small><br>${data.message}`;
    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
  }
  
  function addImageMessage(data, isSelf=false) {
    let chatBox = document.getElementById("chat-box");
    let msgDiv = document.createElement("div");
    msgDiv.classList.add("message");
    msgDiv.classList.add(isSelf ? "sent" : "received");
    msgDiv.innerHTML = `<strong>${data.nickname}</strong> <small>${data.timestamp}</small><br><img src="${data.data}" alt="obrazek" style="max-width: 100%;">`;
    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
  }
  
  function addNotification(text) {
    let chatBox = document.getElementById("chat-box");
    let notifDiv = document.createElement("div");
    notifDiv.classList.add("notification");
    notifDiv.innerText = text;
    chatBox.appendChild(notifDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
  }
</script>
</body>
</html>
"""

class ConnectionManager:
    def __init__(self):
        # Słownik: klucz = nazwa pokoju, wartość = lista krotek (websocket, nickname)
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

manager = ConnectionManager()

@app.get("/")
async def get():
    return HTMLResponse(html)

@app.websocket("/ws/{room}/{nickname}")
async def websocket_endpoint(websocket: WebSocket, room: str, nickname: str):
    await manager.connect(room, websocket, nickname)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                data_json = json.loads(data)
            except Exception as e:
                continue

            # Rozróżniamy typy wiadomości
            if data_json.get("type") == "chat":
                # Wiadomość tekstowa – broadcast do wszystkich w pokoju
                await manager.broadcast(room, data_json)
            elif data_json.get("type") == "typing":
                # Powiadomienie, że użytkownik pisze
                await manager.broadcast(room, data_json)
            elif data_json.get("type") == "notification":
                # Powiadomienia systemowe (join/leave)
                await manager.broadcast(room, data_json)
            elif data_json.get("type") == "image":
                # Wiadomość zawierająca obrazek
                await manager.broadcast(room, data_json)
    except WebSocketDisconnect:
        manager.disconnect(room, websocket)
        notif = {
            "type": "notification",
            "message": f"{nickname} opuścił pokój {room}"
        }
        await manager.broadcast(room, notif)
