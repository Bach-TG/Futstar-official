# websocket_server.py
import asyncio
import json

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from calculate_auto_fill import realtime_momentum_loop
from websocket_client import fetch_url_from_mongo

app = FastAPI()

# match_id -> set(WebSocket)
match_clients: dict[str, set[WebSocket]] = {}

# match_id -> asyncio.Task (crawler+momentum)
match_tasks: dict[str, asyncio.Task] = {}


# ============================================================
#   START PIPELINE FOR A MATCH
# ============================================================
async def start_match_pipeline(match_id: str, db_name: str, match_url: str):
    if match_id in match_tasks:
        print(f"[Match {match_id}] 🟡 already running")
        return

    print(f"[Match {match_id}] 🚀 Pipeline started — URL={match_url}")

    async def _runner():
        try:
            async for data in realtime_momentum_loop(
                match_url=match_url, db_name=db_name
            ):
                await broadcast_to_match(match_id, data)
        except Exception as e:
            print(f"[Match {match_id}] ❌ Crawler error: {e}")
        finally:
            print(f"[Match {match_id}] 🛑 Pipeline stopped")
            match_tasks.pop(match_id, None)

    match_tasks[match_id] = asyncio.create_task(_runner())


# ============================================================
#   BROADCAST TO ALL WS CLIENTS OF THIS MATCH
# ============================================================
async def broadcast_to_match(match_id: str, data: dict):
    clients = match_clients.get(match_id)
    if not clients:
        return

    alive = set()
    for ws in clients:
        try:
            await ws.send_json(data)
            alive.add(ws)
        except:
            pass

    match_clients[match_id] = alive


# ============================================================
#   SINGLE WEBSOCKET ENDPOINT
#   /ws/momentum/{match_id}
# ============================================================
@app.websocket("/ws/momentum/{match_id}")
async def ws_momentum(ws: WebSocket, match_id: str):
    await ws.accept()
    print(f"[WS] 🔌 Client joined -> match_id={match_id}")

    # Tạo group clients
    match_clients.setdefault(match_id, set()).add(ws)

    # Nếu pipeline chưa chạy -> tự chạy
    if match_id not in match_tasks:
        print(f"[WS] 🧪 First client — starting pipeline for {match_id}")

        url = await fetch_url_from_mongo(match_id)
        if not url:
            await ws.send_json({"error": f"match_id={match_id} has no config"})
        else:
            await start_match_pipeline(match_id, match_id, url)
            # await ws.send_json({"status": "pipeline_started", "url": url})

    # Giữ kết nối mở
    try:
        while True:
            await ws.receive_text()  # giữ connection
    except WebSocketDisconnect:
        print(f"[WS] ❌ Client left match {match_id}")
        match_clients.get(match_id, set()).discard(ws)
    except Exception as e:
        print(f"[WS] ⚠ Error: {e}")
        match_clients.get(match_id, set()).discard(ws)


# ============================================================
# SIMPLE UI
# ============================================================
@app.get("/", response_class=HTMLResponse)
async def ui():
    return """
        <h2>Momentum server running</h2>
        <p>Connect to WebSocket: /ws/momentum/{match_id}</p>
    """


# ============================================================
# ENTRY POINT
# ============================================================
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8088)
