import json
from datetime import datetime, timezone

from pydantic import BaseModel

from clients import Clients
from configs import get_logger
from schemas.mongo.futstar_collections import MatchMetadataDB

logger = get_logger(__name__)
mongo_client = Clients.get_mongo_client()


async def add_a_scheduled_match(
    home_team: str,
    away_team: str,
    competition: str,
    home_team_logo: str,
    away_team_logo: str,
    match_time_year: int,
    match_time_month: int,
    match_time_day: int,
    match_time_hour: int,
    match_time_minute: int,
    opta_url: str,
    mongodb_name: str | None = None,
) -> str:
    
    await mongo_client.initialize()
    match = MatchMetadataDB(
        home_team=home_team,
        away_team=away_team,
        match_time=datetime(year=match_time_year, month=match_time_month, day=match_time_day, hour=match_time_hour, minute=match_time_minute, second=0, tzinfo=timezone.utc),
        status="Scheduled",
        competition=competition,
        home_team_logo=home_team_logo,
        away_team_logo=away_team_logo,
        opta_url=opta_url, 
        mongodb_name=mongodb_name
    )
    await match.insert()
    logger.info(f"Added scheduled match with ID: {match.id}")
    return str(match.id)


if __name__ == "__main__":
    import asyncio

    home_team = input("Enter home team name: ")
    away_team = input("Enter away team name: ")
    competition = input("Enter competition name: ")
    home_team_logo = input("Enter home team logo URL: ")
    away_team_logo = input("Enter away team logo URL: ")
    match_time_year = int(input("Enter match year (YYYY): "))
    match_time_month = int(input("Enter match month (MM): "))
    match_time_day = int(input("Enter match day (DD): "))
    match_time_hour = int(input("Enter match hour (HH, 24-hour format): "))
    match_time_minute = int(input("Enter match minute (MM): "))
    opta_url = input("Enter Opta URL: ")
    home_team_con = home_team.replace(" ", "")
    away_team_con = away_team.replace(" ", "")
    year = str(match_time_year)
    month = str(match_time_month) if match_time_month >=10 else f"0{match_time_month}"
    day = str(match_time_day) if match_time_day >=10 else f"0{match_time_day}"
    match_name_for_crawling = f"{year}-{month}-{day}-{home_team_con}-{away_team_con}"
    match_id = asyncio.run(add_a_scheduled_match(
        home_team,
        away_team,
        competition,
        home_team_logo,
        away_team_logo,
        match_time_year,
        match_time_month,
        match_time_day,
        match_time_hour,
        match_time_minute,
        opta_url,
        mongodb_name=match_name_for_crawling
    ))
    logger.info(f"Scheduled match added with ID: {match_id}")
    
    print(f"Match name for crawling: {match_name_for_crawling}")