import asyncio
import json
from datetime import datetime, timedelta, timezone
from typing import Literal
from uuid import UUID

import redis.asyncio as redis
from beanie.operators import And

from clients import Clients
from configs import get_logger, redis_config
from data_ingestion.momentum_ingestion import run_ingestion_all_matches
from hooks.error import ResourceNotFound
from schemas.matches import MatchEvents, MatchMetadata, MatchStats
from schemas.momentum import MomentumIndex
from schemas.mongo.collections import MatchMetadataDB

logger = get_logger(__name__)
mongo_client = Clients.get_mongo_client()

REDIS_DB_URL = f"redis://{redis_config.host}:{redis_config.port}/0"

class MatchOperations:
    @staticmethod
    async def get_match_metadata(match_id: str) -> MatchMetadata:
        match = await MatchMetadataDB.find_one(
            MatchMetadataDB.id == UUID(match_id)
        )
        if not match:
            logger.error(f"Match with ID {match_id} not found.")
            raise ResourceNotFound(f"Match with ID {match_id} not found.")
        match_metadata = MatchMetadata(
            status=match.status,
            match_id=str(match.id),
            home_team=match.home_team,
            away_team=match.away_team,
            competition=match.competition,
            home_team_logo=match.home_team_logo,
            away_team_logo=match.away_team_logo,
            match_date=match.match_time.isoformat() if match.match_time else None,
            home_team_score=None,
            away_team_score=None,
            time_in_match=None,
            momentum_value=None
        )
        return match_metadata

    @staticmethod
    async def get_match(status: Literal["Scheduled", "Live", "Ended", "Testing"] | None = None) -> list[MatchMetadata]:
        if status:
            matches_cursor = MatchMetadataDB.find(
                MatchMetadataDB.status == status
            )
        else:
            matches_cursor = MatchMetadataDB.find()
        r: redis.Redis = redis.from_url(REDIS_DB_URL, encoding="utf-8", decode_responses=True)
        matches: list[MatchMetadata] = []
        async for match in matches_cursor:
            match_metadata = MatchMetadata(
                status=match.status,
                match_id=str(match.id),
                home_team=match.home_team,
                away_team=match.away_team,
                competition=match.competition,
                home_team_logo=match.home_team_logo,
                away_team_logo=match.away_team_logo,
                match_date=match.match_time.isoformat() if match.match_time else None,
                home_team_score=None,
                away_team_score=None,
                time_in_match=None,
                momentum_value=None
            )
            cache_key_latest = f"momentum:{match_metadata.match_id}:latest"
            if match_metadata.status == "Live":
                data = await r.get(cache_key_latest)
                if data:
                    try:
                        momentum_index_dict = json.loads(data)
                        match_metadata.momentum_value = momentum_index_dict["momentum_value"]
                        match_metadata.home_team_score = momentum_index_dict["home_goals"]
                        match_metadata.away_team_score = momentum_index_dict["away_goals"]
                        match_metadata.time_in_match = momentum_index_dict["time_in_match"]
                    except Exception as e:
                        logger.error(f"Error parsing momentum data for match {match.id}: {e}", exc_info=True)

            matches.append(match_metadata)
        if status and status == "Scheduled":
            matches.sort(key=lambda x: x.match_date or "")
        return matches
            

    @staticmethod
    async def checking_live_matches():
        scheduled_matches = await MatchMetadataDB.find(MatchMetadataDB.status == "Scheduled").to_list()
        ingestion_match_ids: list[str] = []
        for match in scheduled_matches:
            match_time = match.match_time
            if match_time and match_time.tzinfo is None:
                match_time = match_time.replace(tzinfo=timezone.utc)
            if match_time and datetime.now(timezone.utc) + timedelta(minutes=5) > match_time:
                match.status = "Live"
                await match.save()
                ingestion_match_ids.append(str(match.id))
                logger.info(f"Updated match {match.id} status to Live")

        await asyncio.sleep(100)
        if ingestion_match_ids:
            logger.info(f"Starting momentum ingestion for matches: {ingestion_match_ids}")
            await run_ingestion_all_matches(ingestion_match_ids)
        else:
            logger.info("No matches to start ingestion for.")
        
    