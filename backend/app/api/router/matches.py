import asyncio
from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, HTTPException, status

from backend.matches import MatchOperations
from hooks.error import ResourceNotFound
from schemas.matches import Event, MatchEvents, MatchMetadata, MatchStats, TeamStats

router = APIRouter(
    prefix="/matches",
    tags=["matches"],
)


@router.post("/refresh_matches_status", status_code=status.HTTP_204_NO_CONTENT)
async def refresh_matches_status():
    """**Trigger a refresh of all match statuses.**
    This endpoint initiates an asynchronous process to update the status of all matches
    in the system. It does not return any data but confirms that the refresh process has started.
    """
    _ = asyncio.create_task(MatchOperations.checking_live_matches())
    return

@router.get("/metadata", response_model=MatchMetadata, status_code=status.HTTP_200_OK)
async def get_match_metadata(match_id: str):
    """**Fetch match metadata by match ID.**
    Inputs:
    - **match_id**: Unique identifier for the match.
    Returns:
    - **MatchMetadata**: Metadata information about the match.
        - `status`: 'Scheduled', 'Live', 'Ended', or 'Testing'
        - `match_id`: Unique identifier for the match.
        - `home_team`: Name of the home team.
        - `away_team`: Name of the away team.
        - `competition`: Name of the competition.
        - `home_team_logo`: URL to the home team's logo.
        - `away_team_logo`: URL to the away team's logo.
        - `match_date`: Date and time of the match.
        - `home_team_score`: Current score of the home team (if status is 'Live' or 'Ended').
        - `away_team_score`: Current score of the away team (if status is 'Live' or 'Ended').
        - `time_in_match`: Current time in the match (if status is 'Live').
    """
    try:
        return await MatchOperations.get_match_metadata(match_id)
    except ResourceNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/all", response_model=dict[str, MatchMetadata], status_code=status.HTTP_200_OK)
async def get_all_matches(status: Literal["Scheduled", "Live", "Ended", "Testing"] | None = None):
    """**Fetch all matches, optionally filtered by status.**
    Inputs:
    - **status**: (Optional) Filter matches by status ('Scheduled', 'Live', 'Ended', 'Testing').
    Returns:
    - **dict[str, MatchMetadata]**: Dictionary of match IDs to MatchMetadata objects.
        - Each MatchMetadata contains:
            - `status`: 'Scheduled', 'Live', 'Ended', or 'Testing'
            - `match_id`: Unique identifier for the match.
            - `home_team`: Name of the home team.
            - `away_team`: Name of the away team.
            - `competition`: Name of the competition.
            - `home_team_logo`: URL to the home team's logo.
            - `away_team_logo`: URL to the away team's logo.
            - `match_date`: Date and time of the match.
            - `home_team_score`: Current score of the home team (if status is 'Live or 'Ended').
            - `away_team_score`: Current score of the away team (if status is 'Live' or 'Ended').
            - `time_in_match`: Current time in the match (if status is 'Live').
            - `momentum_value`: Current momentum value of the live match (if available).
    """
    matches = await MatchOperations.get_match(status)
    return {match.match_id: match for match in matches}
