# config_ws_server.py
import asyncio
import json

from aiohttp import web

from clients import Clients

# Mongo client (đã theo chuẩn code của bạn)
mongo_client = Clients.get_mongo_client()


async def fetch_url_from_mongo(match_id: str) -> str | None:
    """
    - Kết nối tới DB có tên = match_id
    - Đọc collection 'match_data'
    - Lấy URL trận đấu từ document trong đó
    """
    # 1) chọn DB = match_id
    await mongo_client.initialize(db_name=match_id)

    # 2) collection chứa url
    coll = mongo_client.db["match_data"]

    # Nếu mỗi DB chỉ có 1 document thì có thể dùng find_one({})
    # nhưng mình lọc theo match_id cho rõ ràng:
    doc = await coll.find_one({"match_id": match_id}) or await coll.find_one({})

    if not doc:
        print(f"[Mongo] ⚠️ No match_data found in DB={match_id}")
        return None

    url = doc.get("url")
    print(f"[Mongo] ✅ URL for {match_id} = {url}")
    return url


def create_config_ws_server(start_match_callback):
    async def ws_handler(request):
        match_id = request.match_info.get("match_id")
        print(f"[WS-SERVER] 🔌 New WS client: match_id={match_id}")

        ws = web.WebSocketResponse()
        await ws.prepare(request)

        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                try:
                    try:
                        data = msg.json()
                    except Exception:
                        data = json.loads(msg.data)

                    db_name = data.get("match_id") or match_id
                    if not db_name:
                        await ws.send_json({"error": "missing match_id"})
                        continue

                    print(f"[WS-SERVER] 🎯 Incoming match_id={db_name}")

                    # Lấy URL từ Mongo (có initialize)
                    url = await fetch_url_from_mongo(db_name)
                    if not url:
                        await ws.send_json(
                            {"error": f"db_name={db_name} not found in Mongo"}
                        )
                        continue

                    print(f"[WS-SERVER] 🌐 URL fetched = {url}")

                    # Gọi callback chính của bạn
                    await start_match_callback(db_name, db_name, url)

                    await ws.send_json(
                        {"status": "started", "match_id": db_name, "url": url}
                    )

                except Exception as e:
                    await ws.send_json({"error": str(e)})

            else:
                print(f"[WS-SERVER] ⚠️ WS type={msg.type}")

        print(f"[WS-SERVER] 🔌 Disconnected: {match_id}")
        return ws

    app = web.Application()
    app.add_routes([web.get("/ws/match/{match_id}", ws_handler)])
    return app
