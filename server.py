"""WebSend シグナリングサーバー。

役割はWebRTCのSDP/ICE candidateをルーム内の端末間で中継するだけ。
ファイル・テキストの実データはここを経由しない。DB・ディスク保存も一切行わない
（ルーム状態はプロセスメモリ上の辞書のみで、再起動すれば消える）。
"""
import json
import uuid
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

from stun_server import start_stun_server

app = FastAPI()

STATIC_DIR = Path(__file__).parent / "static"
STUN_PORT = 3478

# room名 -> {client_id: {"ws": WebSocket, "name": str}}
rooms: dict[str, dict[str, dict]] = {}


@app.on_event("startup")
async def launch_stun_server() -> None:
    # mDNS匿名化されたhost candidateしか出せないブラウザ(Haiku OS WebPositive等)でも
    # 実IPアドレスのcandidateを得られるよう、LAN内完結のSTUNサーバーを同居させる。
    app.state.stun_transport = await start_stun_server(port=STUN_PORT)


@app.on_event("shutdown")
async def stop_stun_server() -> None:
    transport = getattr(app.state, "stun_transport", None)
    if transport:
        transport.close()


@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")


async def broadcast(room: str, message: dict, exclude: str | None = None) -> None:
    for cid, peer in list(rooms.get(room, {}).items()):
        if cid == exclude:
            continue
        try:
            await peer["ws"].send_json(message)
        except Exception:
            pass


@app.websocket("/ws/{room}")
async def signaling(websocket: WebSocket, room: str) -> None:
    await websocket.accept()
    client_id = uuid.uuid4().hex[:8]

    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            mtype = msg.get("type")

            if mtype == "join":
                name = str(msg.get("name", "unknown"))[:64]
                room_peers = rooms.setdefault(room, {})
                existing = [{"id": cid, "name": p["name"]} for cid, p in room_peers.items()]
                room_peers[client_id] = {"ws": websocket, "name": name}
                await websocket.send_json({"type": "joined", "selfId": client_id, "peers": existing})
                await broadcast(room, {"type": "peer-joined", "id": client_id, "name": name}, exclude=client_id)

            elif mtype in ("offer", "answer", "ice-candidate"):
                target = rooms.get(room, {}).get(msg.get("to"))
                if target:
                    await target["ws"].send_json({**msg, "from": client_id})

    except WebSocketDisconnect:
        pass
    finally:
        room_peers = rooms.get(room)
        if room_peers and client_id in room_peers:
            del room_peers[client_id]
            if room_peers:
                await broadcast(room, {"type": "peer-left", "id": client_id})
            else:
                rooms.pop(room, None)
