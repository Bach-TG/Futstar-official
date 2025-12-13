import asyncio
import json
import os
import time
from uuid import UUID

import redis.asyncio as redis
import websockets
from websockets.exceptions import ConnectionClosedError

from backend.users import UserMissionCheckingOperations
from configs import data_provider_config, get_logger, redis_config
from schemas.momentum import MomentumIndex
from schemas.mongo.collections import MatchMetadataDB

logger = get_logger(__name__)

REDIS_DB_URL = f"redis://{redis_config.host}:{redis_config.port}/0"
WS_PROVIDER_URL = f"ws://{data_provider_config.host}:{data_provider_config.port}/ws/momentum/" if data_provider_config.use == "ip" else f"wss://{data_provider_config.domain}/ws/momentum/"

MAX_DURATION_SECONDS = 3 * 60 * 60  # 3 hours
IDLE_TIMEOUT_SECONDS = 1 * 60 * 60  # 1 hour
TTL_SECONDS = 6 * 60 * 60  # 6 hours


async def checking_ended_match(match_id: str):
    match = await MatchMetadataDB.find_one(
        MatchMetadataDB.id == UUID(match_id)        
    )
    if not match:
        logger.error(f"Live match with ID {match_id} not found for ending check.")
        return
    match.status = "Ended"
    await match.save()
    logger.info(f"Updated match {match.id} status to Ended")

async def monitor_single_match(r: redis.Redis, match_id: str):
    match = await MatchMetadataDB.find_one(
        MatchMetadataDB.id == UUID(match_id)        
    )
    if not match:
        logger.error(f"Match with ID {match_id} not found for monitoring.")
        return
    ws_url = WS_PROVIDER_URL + match.mongodb_name if match.mongodb_name else match_id

    channel_name = f"momentum:{match_id}"
    cache_key_latest = f"momentum:{match_id}:latest"
    history_key = f"momentum:{match_id}:history"

    # await r.delete(history_key)

    logger.info(f"Starting monitoring for match {match_id} via {ws_url}")

    start_time = time.time()

    try:
        async with websockets.connect(ws_url) as websocket:
            logger.info(f"Connected to WebSocket for match {match_id}")

            while True:
                elapsed_time = time.time() - start_time
                if elapsed_time > MAX_DURATION_SECONDS:
                    logger.info(f"Max duration reached for match {match_id}. Ending monitoring.")
                    break

                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=IDLE_TIMEOUT_SECONDS)

                    current_ts = time.time()
                    logger.info(f"Received data for match {match_id} at {current_ts}: {message}")
                    try:
                        if message.find("Half Time") != -1:
                            logger.info(f"Match {match_id} has reached Half Time.")



                        async with r.pipeline(transaction=True) as pipe:
                            _ = pipe.set(cache_key_latest, message, ex=TTL_SECONDS)
                            _ = pipe.publish(channel_name, message)
                            _ = pipe.zadd(history_key, {message: current_ts})
                            _ = pipe.expire(history_key, TTL_SECONDS)

                            _ = await pipe.execute()
                            logger.info("Cached and published momentum data")
                        
                        if message.find("Full Time") != -1:
                            logger.info(f"Match {match_id} has ended with Full Time. Ending monitoring.")
                            await asyncio.sleep(5)  # Wait a bit before finalizing
                            await checking_ended_match(match_id)
                            _ = asyncio.create_task(UserMissionCheckingOperations.check_mission_podium_finish(match_id=match_id))
                            break
                    except Exception as e:
                        logger.error(f"Error processing momentum data for match {match_id}: {e}", exc_info=True)

                    
                
                except asyncio.TimeoutError:
                    logger.info(f"No data received for match {match_id} in the last {IDLE_TIMEOUT_SECONDS} seconds. Ending monitoring.")
                    break
    except (ConnectionClosedError) as e:
        logger.error(f"WebSocket connection closed unexpectedly for match {match_id}: {e}")
    except Exception as e:
        logger.error(f"Error while monitoring match {match_id}: {e}", exc_info=True)
    finally:
        logger.info(f"Stopped monitoring for match {match_id}")


async def run_ingestion_all_matches(match_ids: list[str]):
    r = redis.from_url(REDIS_DB_URL, encoding="utf-8", decode_responses=True)

    tasks = [monitor_single_match(r, match_id) for match_id in match_ids]

    if tasks:
        _ = await asyncio.gather(*tasks)
    else:
        logger.warning("No match IDs provided for ingestion.")

    await r.close()

async def run_ingestion(match_id: str):
    r = redis.from_url(REDIS_DB_URL, encoding="utf-8", decode_responses=True)

    await monitor_single_match(r, match_id)

    await r.close()

