from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from typing import List

app = FastAPI()

html = """
<!DOCTYPE html>
<html>
<head>
    <title>Chat</title>
</head>
<body>
    <h1>WebSocket Chat</h1>
    <form id="form">
        <input type="text" id="roomName" placeholder="Enter Room Name" autocomplete="off"/>
        <input type="text" id="messageText" placeholder="Enter Message" autocomplete="off"/>
        <button>Send</button>
    </form>
    <ul id="messages">
    </ul>
    <script>
        var ws;
        document.getElementById('form').onsubmit = function(event) {
            var roomName = document.getElementById("roomName").value;
            var input = document.getElementById("messageText");
            if (!ws || ws.readyState === WebSocket.CLOSED) {
                ws = new WebSocket("ws://localhost:8000/ws/" + roomName);
                ws.onmessage = function(event) {
                    var messages = document.getElementById('messages')
                    var message = document.createElement('li')
                    var content = document.createTextNode(event.data)
                    message.appendChild(content)
                    messages.appendChild(message)
                };
            }
            ws.send(input.value);
            input.value = ''
            event.preventDefault();
        };
    </script>
</body>
</html>
"""

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room: str):
        await websocket.accept()
        if room not in self.active_connections:
            self.active_connections[room] = []
        self.active_connections[room].append(websocket)

    def disconnect(self, websocket: WebSocket, room: str):
        self.active_connections[room].remove(websocket)
        if not self.active_connections[room]:
            del self.active_connections[room]

    async def broadcast(self, message: str, room: str):
        for connection in self.active_connections.get(room, []):
            await connection.send_text(message)

manager = ConnectionManager()

@app.get("/")
async def get():
    return HTMLResponse(html)

@app.websocket("/ws/{room}")
async def websocket_endpoint(websocket: WebSocket, room: str):
    await manager.connect(websocket, room)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"Message in {room}: {data}", room)
    except WebSocketDisconnect:
        manager.disconnect(websocket, room)
