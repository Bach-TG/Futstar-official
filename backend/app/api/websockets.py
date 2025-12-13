import asyncio
import json
from uuid import UUID

import redis.asyncio as redis
from fastapi import (
    APIRouter,
    Query,
    Request,
    WebSocket,
    WebSocketDisconnect,
    WebSocketException,
)

from backend.momentum import MomentumOperations
from backend.users import UserOperations
from configs import get_logger
from schemas.momentum import MomentumIndex, MomentumPositions, PositionPnlUpdate
from schemas.mongo.collections import PositionHistoryDB
from utils.calculate import calculate_pnl, next_second_time_in_match

logger = get_logger(__name__)
router = APIRouter(tags=["websockets"])


@router.websocket("/momentum/{match_id}/ws")
async def momentum_websocket_endpoint(websocket: WebSocket, match_id: str):
    await websocket.accept()
    r: redis.Redis = websocket.app.state.redis

    channel_name = f"momentum:{match_id}"
    cache_key_latest = f"momentum:{match_id}:latest"

    client_info = f"{websocket.client.host} -> Match: {match_id}"
    logger.info(f"Connected: {client_info}")


    pubsub = r.pubsub()

    try:
        latest_data = await r.get(cache_key_latest)
        if latest_data:
            await websocket.send_text(latest_data)
        
        await pubsub.subscribe(channel_name)

        async for message in pubsub.listen():
            if message["type"] == "message":
                data = message["data"]
                await websocket.send_text(data)

    except WebSocketException as e:
        logger.error(f"WebSocket exception for {client_info}: {e}")
    except Exception as e:
        logger.error(f"Error in WebSocket for {client_info}: {e}", exc_info=True)
    finally:
        if pubsub:
            await pubsub.unsubscribe(channel_name)
            await pubsub.close()
        logger.info(f"Disconnected: {client_info}")


@router.websocket("/position/{position_id}/ws")
async def position_websocket_endpoint(websocket: WebSocket, position_id: str):
    await websocket.accept()
    r: redis.Redis = websocket.app.state.redis

    position_data_key = f"position:data:{position_id}"

    try:
        raw_data = await r.get(position_data_key)
        if not raw_data:
            logger.error(f"Position with ID {position_id} not found in Redis.")
            await websocket.close(code=4004, reason="Position not found")
            return
        position_data = MomentumPositions.model_validate(json.loads(raw_data))
        pnl_updating_channel_name = f"position:pnl_updates:{position_data.position_id}"
        pnl_latest_cache_key = f"position:pnl:{position_data.position_id}:latest"
        position_ids_key = f"position:ids:{position_data.user_id}:{position_data.match_id}"
        pubsub = r.pubsub()
        latest_pnl_data_raw = await r.get(pnl_latest_cache_key)
        if latest_pnl_data_raw:
            await websocket.send_text(latest_pnl_data_raw)
        await pubsub.subscribe(pnl_updating_channel_name)

        async for message in pubsub.listen():
            if message["type"] == "message":
                data = message["data"]
                await websocket.send_text(data)
        
        
    except WebSocketDisconnect as e:
        logger.info(f"WebSocket disconnected for position ID {position_id}: {e}")
    except Exception as e:
        logger.error(f"Error in WebSocket for position ID {position_id}: {e}", exc_info=True)
    finally:
        logger.info(f"WebSocket connection closed for position ID {position_id}")
        



@router.websocket("/testing/momentum/{match_id}/ws")
async def testing_momentum_websocket_endpoint(websocket: WebSocket, match_id: str):
    await websocket.accept()

    monentum_data_list = []
    try:
        with open(f"momentum_index_{match_id}.json", "r") as f:
            monentum_data_list = json.load(f)
            logger.info(f"Loaded testing momentum data for match ID {match_id}")
    except Exception as e:
        logger.error(f"Error loading testing momentum data for match ID {match_id}: {e}")
        await websocket.close(code=4004, reason=f"Testing data not found for match ID {match_id}")
        return
    
    monentum_data_dict = {data["time_in_match"]: data for data in monentum_data_list}
    logger.info(f"Testing WebSocket connected for match ID {match_id}")

    try:
        for key in monentum_data_dict.keys():
            data = monentum_data_dict[key]
            return_data = MomentumIndex(
                time_in_match=data["time_in_match"],
                momentum_value=data["momentum_index"],
                home_goals=data["home_goals"],
                away_goals=data["away_goals"],
            )
            await websocket.send_text(return_data.model_dump_json())
            await asyncio.sleep(1)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for match {match_id}")
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error for match {match_id}: {e}")
        await websocket.send_json({"error": "Invalid JSON data"})
        await websocket.close(code=1008)
    except Exception as e:
        logger.error(f"Unexpected error in momentum websocket: {e}", exc_info=True)
        try:
            await websocket.send_json({"error": str(e)})
            await websocket.close(code=1011)  # Internal error
        except Exception:
            pass
    finally:
        logger.info(f"Testing WebSocket connection closed for match ID {match_id}")


@router.websocket("/testing/position/{match_id}/{time_in_match}/{duration}/{amount_str}/{type}/ws")
async def testing_position_websocket_endpoint(websocket: WebSocket, match_id: str, time_in_match: str, duration: str, amount_str: str, type: str):
    await websocket.accept()

    monentum_data_list = []
    try:
        with open(f"momentum_index_{match_id}.json", "r") as f:
            monentum_data_list = json.load(f)
            logger.info(f"Loaded testing momentum data for match ID {match_id}")
    except Exception as e:
        logger.error(f"Error loading testing momentum data for match ID {match_id}: {e}")
        await websocket.close(code=4004, reason=f"Testing data not found for match ID {match_id}")
        return
    
    monentum_data_dict = {data["time_in_match"]: data for data in monentum_data_list}
    logger.info(f"Testing Position WebSocket connected for time_in_match {time_in_match}, duration {duration}, amount {amount_str}, type {type} on match ID {match_id}")
    entry_value = monentum_data_dict.get(time_in_match, {}).get("momentum_index", 0.0)
    amount = float(amount_str)

    remaining_time = int(duration[:-1]) if duration.endswith('s') else int(duration[:-1]) * 60
    try:
        doing: bool = False
        for key in monentum_data_dict.keys():
            if key == time_in_match:
                doing = True
            if not doing:
                continue
            data = monentum_data_dict[key]
            current_momentum_value = data["momentum_index"]
            pnl_percentage = await calculate_pnl(
                entry=entry_value,
                current=current_momentum_value,
                D=1 if type.lower() == "long" else -1
            ) * 100.0
            pnl_payout = (pnl_percentage / 100) * amount
            return_data = PositionPnlUpdate(
                position_id="testing-position-123",
                pnl_percentage=pnl_percentage,
                pnl_payout=pnl_payout,
                remaining_time=remaining_time,
                current_value=current_momentum_value if current_momentum_value else 0.0,
                entry_value=entry_value if entry_value else 0.0,
                entry_time=time_in_match,
                current_time=data["time_in_match"] if data["time_in_match"] else time_in_match,
                current_bonus_points_reward=pnl_percentage if pnl_percentage > 0 else 0.0
            )
            remaining_time -= 1
            await websocket.send_text(return_data.model_dump_json())
            if remaining_time < 0:
                break
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for testing position")
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error for testing position: {e}")
        await websocket.send_json({"error": "Invalid JSON data"})
        await websocket.close(code=1008)
    except Exception as e:
        logger.error(f"Unexpected error in testing position websocket: {e}", exc_info=True)
        try:
            await websocket.send_json({"error": str(e)})
            await websocket.close(code=1011)  # Internal error
        except Exception:
            pass
    finally:
        logger.info(f"Testing Position WebSocket connection closed")
