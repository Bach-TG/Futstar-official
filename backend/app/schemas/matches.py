from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class MatchMetadata(BaseModel):
    status: Literal['Scheduled', 'Live', 'Ended', 'Testing']
    match_id: str
    home_team: str
    away_team: str
    competition: str
    home_team_logo: str
    away_team_logo: str
    match_date: datetime | None = None  # ISO 8601 format
    home_team_score: int | None = None
    away_team_score: int | None = None
    momentum_value: float | None = None
    time_in_match: str | None = None  # e.g., "45:00" for live matches
    
class Event(BaseModel):
    event_type: Literal['Goal', 'Yellow Card', 'Red Card', 'Substitution']
    team: str
    player: str
    other_player: str | None = None  # For substitutions
    

class MatchEvents(BaseModel):
    events: dict[str, list[Event]]  # Keyed by minute of the match

class TeamStats(BaseModel):
    shots: int
    shots_on_target: int
    possession_percentage: float
    passes: int
    pass_accuracy: float
    fouls: int
    yellow_cards: int
    red_cards: int
    offsides: int
    corners: int

class MatchStats(BaseModel):
    time_in_match: str  # e.g., "45:00"
    home_team_stats: TeamStats
    away_team_stats: TeamStats
