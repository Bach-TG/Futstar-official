import asyncio
import json
import time
from datetime import datetime
from typing import Literal
from uuid import UUID

import redis.asyncio as redis
from beanie.operators import And
from pydantic import BaseModel

from backend.users import UserMissionCheckingOperations, UserOperations
from clients import Clients
from configs import get_logger, redis_config
from hooks.error import ResourceNotFound
from schemas.momentum import MomentumIndex, MomentumPositions, PositionPnlUpdate
from schemas.mongo.collections import MatchMetadataDB, PositionHistoryDB, UserMetadataDB
from schemas.users import UserMetadata
from utils.calculate import calculate_pnl

TTL_SECONDS = 15 * 60  # 45 minutes

logger = get_logger(__name__)
mongo_client = Clients.get_mongo_client()


class UserTotalPnl(BaseModel):
    user: UserMetadata
    total_pnl: float


class MomentumOperations:

    

    @staticmethod
    async def save_position_to_database(position: MomentumPositions):
        new_position = PositionHistoryDB(
            id=UUID(position.position_id),
            type=position.type,
            amount=position.amount,
            timestamp=position.timestamp,
            duration=position.duration,
            entry_value=position.entry_value,
            closed_value=position.closed_value,
            pnl_percentage=position.pnl_percentage,
            user_id=position.user_id,
            match_id=position.match_id,
            status=position.status,
            time_in_match_entry=position.time_in_match_entry,
            time_in_match_closed=position.time_in_match_closed,
            bonus_points_rewarded=position.bonus_points_rewarded
        )
        await new_position.insert()
        logger.info(f"Saved position {position.position_id} to database.")
        _ = asyncio.create_task(UserMissionCheckingOperations.check_mission_first_kick(user_id=position.user_id))
        _ = asyncio.create_task(UserMissionCheckingOperations.check_mission_hot_streak_200(user_id=position.user_id, match_id=position.match_id))

    


    @staticmethod
    async def calculate_pnl_background(position_data: MomentumPositions):
        remaining_time = int(position_data.duration[:-1]) if position_data.duration.endswith('s') else int(position_data.duration[:-1]) * 60
        pnl_updating_channel_name = f"position:pnl_updates:{position_data.position_id}"
        pnl_latest_cache_key = f"position:pnl:{position_data.position_id}:latest"
        momentum_cache_key_latest = f"momentum:{position_data.match_id}:latest"
        position_data_key = f"position:data:{position_data.position_id}"
        position_ids_key = f"position:ids:{position_data.user_id}:{position_data.match_id}"
        REDIS_DB_URL = f"redis://{redis_config.host}:{redis_config.port}/0"
        logger.info(f"Starting PnL calculation for position {position_data.position_id} with remaining time {remaining_time} seconds.")
        r: redis.Redis = redis.from_url(REDIS_DB_URL, encoding="utf-8", decode_responses=True)
        while remaining_time > 0:
            current_momentum_raw_data = await r.get(momentum_cache_key_latest)
            if not current_momentum_raw_data:
                await asyncio.sleep(1)
                continue
            current_momentum_data = MomentumIndex.model_validate(json.loads(current_momentum_raw_data))
            if current_momentum_data.time_in_match == position_data.time_in_match_entry:
                await asyncio.sleep(1)
                continue
            pnl_percentage = await calculate_pnl(
                entry=position_data.entry_value,
                current=current_momentum_data.momentum_value,
                D=1 if position_data.type == "Long" else -1
            ) * 100.0
            pnl_payout = (pnl_percentage / 100) * position_data.amount

            remaining_time -= 1
            pnl_data = PositionPnlUpdate(
                position_id=position_data.position_id,
                pnl_percentage=pnl_percentage,
                pnl_payout=pnl_payout,
                remaining_time=remaining_time,
                current_value=current_momentum_data.momentum_value,
                entry_value=position_data.entry_value,
                entry_time=position_data.time_in_match_entry,
                current_time=current_momentum_data.time_in_match,
                current_bonus_points_reward=max(round(pnl_percentage * 10), 0)
            )
            async with r.pipeline(transaction=True) as pipe:
                await pipe.publish(pnl_updating_channel_name, pnl_data.model_dump_json())
                await pipe.set(pnl_latest_cache_key, pnl_data.model_dump_json(), ex=TTL_SECONDS)
                _ = await pipe.execute()
                logger.info(f"Published PnL update for position {position_data.position_id} at time in match {current_momentum_data.time_in_match}")
            if remaining_time <= 0:
                position_data.closed_value = current_momentum_data.momentum_value
                position_data.time_in_match_closed = current_momentum_data.time_in_match
                position_data.status = "Closed"
                position_data.bonus_points_rewarded = max(round(pnl_percentage * 10), 0)
                position_data.pnl_percentage = pnl_percentage
                await MomentumOperations.save_position_to_database(position_data)
                await UserOperations.update_user_experience_points(
                    user_id=position_data.user_id,
                    points=round(position_data.bonus_points_rewarded)
                )
                await UserOperations.update_user_bonus_points(
                    user_id=position_data.user_id,
                    points=round(position_data.bonus_points_rewarded)
                )
                async with r.pipeline(transaction=True) as pipe:
                    await pipe.delete(position_data_key)
                    _ = pipe.srem(position_ids_key, position_data.position_id)
                    _ = await pipe.execute()
                    logger.info(f"Position {position_data.position_id} closed and removed from Redis.")
                break
            await asyncio.sleep(1)

        logger.info(f"Completed PnL calculation for position {position_data.position_id}")



    @staticmethod
    async def get_total_pnl_ranking(match_id: str, top_n: int = 100) -> dict[int, UserTotalPnl]:
        match = await MatchMetadataDB.find_one(MatchMetadataDB.id == UUID(match_id))
        if not match:
            logger.error(f"Match with ID {match_id} not found for PnL ranking.")
            raise ResourceNotFound(f"Match with ID {match_id} not found.")
        if match.status == "Scheduled":
            logger.error(f"Match with ID {match_id} has not started yet for PnL ranking.")
            raise ResourceNotFound(f"Match with ID {match_id} has not started yet.")
        positions_cursor = PositionHistoryDB.find(
            PositionHistoryDB.match_id == match_id
        )
        user_total_pnl: dict[str, float] = {}
        async for position in positions_cursor:
            if position.user_id not in user_total_pnl:
                user_total_pnl[position.user_id] = 0.0
            user_total_pnl[position.user_id] += position.pnl_percentage

        sorted_users = sorted(user_total_pnl.items(), key=lambda item: item[1], reverse=True)[:top_n]
        ranking: dict[int, UserTotalPnl] = {}
        rank = 1
        for user_id, total_pnl in sorted_users:
            try:
                user_metadata = await UserOperations.get_user_metadata(user_id)
                ranking[rank] = UserTotalPnl(user=user_metadata, total_pnl=total_pnl)
                rank += 1
            except ResourceNotFound as e:
                logger.error(f"User with ID {user_id} not found while compiling PnL ranking: {e}")
                continue
            
        return ranking