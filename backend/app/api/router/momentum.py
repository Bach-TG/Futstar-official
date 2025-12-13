import asyncio
import json
import time
from datetime import datetime, timezone
from typing import Literal
from uuid import UUID

import redis.asyncio as redis
from fastapi import APIRouter, HTTPException, Query, Request, status

from backend.momentum import MomentumOperations, UserTotalPnl
from configs import get_logger
from data_ingestion.momentum_ingestion import run_ingestion
from hooks.error import ResourceNotFound
from schemas.momentum import MomentumIndex, MomentumPositions, PositionPnlUpdate
from schemas.response import ApiResponse
from schemas.users import UserMetadata
from utils import hasher

logger = get_logger(__name__)

router = APIRouter(
    prefix="/momentum",
    tags=["momentum"],
)

POSITION_TTL_SECONDS = 45 * 60  # 45 minutes


@router.get("/start_ingestion", status_code=status.HTTP_200_OK)
async def start_momentum_data_ingestion_for_a_match(match_id: str):
    """**Start momentum data ingestion for a specific match.**
    Inputs:
    - **match_id**: Unique identifier for the match.
    Returns:
    - **str**: Confirmation message indicating that ingestion has started.
    """
    _ = asyncio.create_task(run_ingestion(match_id))
    logger.info(f"Started momentum data ingestion for match_id: {match_id}")
    return f"Momentum data ingestion started for match_id: {match_id}"



@router.get("/full_match_index", response_model=list[MomentumIndex], status_code=status.HTTP_200_OK)
async def get_momentum_index_full_match(request: Request, match_id: str = Query(..., description="Unique identifier for the match")):
    """**Fetch momentum index data for a specific match full match interval.**
    Inputs:
    - **match_id**: Unique identifier for the match.
    Returns:
    - **list[MomentumIndex]**: List of MomentumIndex objects representing momentum over time.
        - Each MomentumIndex contains:
            - `time_in_match`: Time in the match (e.g., "45:00").
            - `momentum_value`: Momentum value at that time (e.g., 0.75 representing 75% momentum).
    """
    r: redis.Redis = request.app.state.redis
    history_key = f"momentum:{match_id}:history"
    raw_history = await r.zrange(history_key, 0, -1)
    logger.info(f"Fetched {len(raw_history)} momentum index entries for match_id: {match_id}")
    momentum_index: list[MomentumIndex] = []
    for item in raw_history:
        item_json = json.loads(item)
        momentum_index.append(
            MomentumIndex(
                time_in_match=item_json["time_in_match"],
                momentum_value=item_json["momentum_value"],
                home_goals=item_json["home_goals"],
                away_goals=item_json["away_goals"]
            )
        )
    return momentum_index







@router.get("/opening_positions", response_model=dict[str, MomentumPositions], status_code=status.HTTP_200_OK)
async def get_opening_positions(request: Request, user_id: str, match_id: str):
    """**Fetch user opening momentum positions by user ID and match ID (Long / Short).**
    Inputs:
    - **user_id**: Unique identifier for the user.
    - **match_id**: Unique identifier for the match.
    Returns:
    - Keyed by str (**Position ID**):
        - Each MomentumPositions contains:
            - `position_id`: Unique identifier for the position.
            - `type`: Type of position ('Long' or 'Short').
            - `duration`: Duration of the position. 
            - `entry_value`: Entry value of the position.
            - `closed_value`: Closed value of the position (if closed).
            - `pnl_percentage`: Profit and loss percentage of the position.
            - `amount`: Amount for the position.
            - `timestamp`: Timestamp when the position was created.
            - `user_id`: Unique identifier for the user.
            - `match_id`: Unique identifier for the match.
            - `time_in_match_entry`: Time in match when the position was entered.
            - `time_in_match_closed`: Time in match when the position was closed (if closed).
            - `status`: Status of the position ('Open' or 'Closed').
            - `bonus_points_rewarded`: Bonus points rewarded for this position.
    """
    r: redis.Redis = request.app.state.redis
    position_ids_key = f"position:ids:{user_id}:{match_id}"
    position_ids = await r.smembers(position_ids_key)
    if not position_ids:
        raise HTTPException(status_code=404, detail="No opening positions found for the user in this match.")
    position_data_keys = [f"position:data:{pid}" for pid in position_ids]
    raw_data_list = await r.mget(position_data_keys)
    result: dict[str, MomentumPositions] = {}
    for raw_data in raw_data_list:
        if not raw_data:
            continue
        position = MomentumPositions.model_validate(json.loads(raw_data))
        if position.status == "Open":
            result[position.position_id] = position

    if not result:
        raise HTTPException(status_code=404, detail="No opening positions found for the user in this match.")
    return result





@router.post("/positions", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def create_position(request: Request, user_id: str, match_id: str, time_in_match: str, type: Literal['Long', 'Short'], entry: float, amount: float, duration: Literal["30s", "1m", "2m", "3m", "5m", "10m"] = "5m"):
    """**Create a new momentum position for a user (Long / Short).**
    Inputs:
    - **user_id**: Unique identifier for the user.
    - **match_id**: Unique identifier for the match.
    - **type**: Type of position ('Long' or 'Short').
    - **entry**: Entry of the position.
    - **amount**: Amount for the position.
    - **duration**: Duration of the position ("30s", "1m", "2m", "3m", "5m", "10m"), default is "5m".
    Returns:
    - ApiResponse: Confirmation of position creation.
        - `success`: Indicates if the operation was successful.
        - `status_code`: HTTP status code of the response.
        - `message`: Confirmation message.
        - `data`: Details of the created position including timestamp.
            - Each position includes:
                - `position_id`: Unique identifier for the position.
                - `pnl_percentage`: Initial profit and loss percentage (0.0 at creation).
                - `pnl_payout`: Initial profit and loss payout (0.0 at creation).
                - `remaining_time`: Remaining time for the position in seconds.
                - `current_value`: Current value of the position (same as entry at creation).
                - `entry_value`: Entry value of the position.
                - `entry_time`: Entry time in match.
                - `current_time`: Current time in match.
                - `current_bonus_points_reward`: Current bonus points reward (0.0 at creation).
    """
    timestamp = datetime.now(timezone.utc)
    position_id = str(hasher.get_hash(f"{user_id}-{match_id}-{timestamp.isoformat()}"))

    r: redis.Redis = request.app.state.redis
    
    position_data_key = f"position:data:{position_id}"
    position_ids_key = f"position:ids:{user_id}:{match_id}"

    await r.delete(position_ids_key)  # Clear existing positions for user and match to avoid duplicates

    new_position = MomentumPositions(
        position_id=position_id,
        type=type,
        duration=duration,
        entry_value=entry,
        pnl_percentage=0.0,
        amount=amount,
        timestamp=timestamp.isoformat(),
        user_id=user_id,
        match_id=match_id,
        time_in_match_entry=time_in_match,
        status="Open",
    )
    remaining_time = int(duration[:-1]) if duration.endswith('s') else int(duration[:-1]) * 60
    async with r.pipeline(transaction=True) as pipe:
        _ = pipe.set(position_data_key, new_position.model_dump_json(), ex=remaining_time + 1)
        _ = pipe.sadd(position_ids_key, position_id)
        _ = pipe.expire(position_ids_key, POSITION_TTL_SECONDS)
        _ = await pipe.execute()
        logger.info(f"Created new position with ID {position_id} for user {user_id} on match {match_id}")
    
    _ = asyncio.create_task(MomentumOperations.calculate_pnl_background(new_position))

    position_pnl = PositionPnlUpdate(
        position_id=position_id,
        pnl_payout=0.0,
        pnl_percentage=0.0,
        remaining_time=remaining_time,
        current_bonus_points_reward=0.0,
        current_value=entry,
        entry_value=entry,
        entry_time=time_in_match,
        current_time=time_in_match
    )
    return ApiResponse(
        success=True,
        status_code=status.HTTP_201_CREATED,
        message="Position created successfully.",
        data=position_pnl.model_dump()
    )





@router.get("/total_pnl_ranking", response_model=dict[int, UserTotalPnl], status_code=status.HTTP_200_OK)
async def get_total_pnl_ranking(match_id: str, top_n: int = 100):
    """**Fetch total PnL ranking for users in a specific match.**
    Inputs:
    - **match_id**: Unique identifier for the match.
    - ( Optional ) **top_n**: Number of top users to return in the ranking, default is 100.
    Returns:
    - Keyed by rank (int):
        - Each UserTotalPnl contains:
            - `user`: UserMetadata object representing the user.
            - `total_pnl`: Total profit and loss percentage for the user in the match.
    """
    try:
        ranking = await MomentumOperations.get_total_pnl_ranking(match_id, top_n)
        return ranking
    except ResourceNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching total PnL ranking for match {match_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")