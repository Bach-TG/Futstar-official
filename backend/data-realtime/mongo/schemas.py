from datetime import datetime
from uuid import UUID

from beanie import Document, Indexed, Link
from pydantic import BaseModel, Field


# ============================
# League
# ============================
class League(BaseModel):
    id: str
    name: str
    countryName: str


# ============================
# Metadata Collections
# ============================
class ClubsMetadata(Document):
    id: UUID
    club_id: str
    name: str
    league: League
    updated_at: datetime

    class Settings:
        name = "clubs_metadata"
        validate_on_save = True


class PlayersMetadata(Document):
    id: UUID
    player_id: str
    name: str
    age: int | None
    height: int | None
    nationality: str | None
    position: str | None
    foot: str | None
    club: Link[ClubsMetadata]
    club_id: str
    updated_at: datetime

    class Settings:
        name = "players_metadata"
        validate_on_save = True


class MatchesMetadata(Document):
    id: UUID
    match_id: str
    date: datetime
    status: str
    home_team: Link[ClubsMetadata]
    away_team: Link[ClubsMetadata]
    home_score: int | None
    away_score: int | None
    competition: str
    updated_at: datetime

    class Settings:
        name = "matches_metadata"
        validate_on_save = True


# =====================================================
# STATS COLLECTIONS — tất cả đều có thêm `timestamp`
# =====================================================


class MatchGeneralStats(Document):
    time_in_match: Indexed(str)
    timestamp: datetime = Field(
        ..., description="Server timestamp when data was recorded"
    )  # NEW

    possession: tuple[int | float | str, int | float | str]
    possession_lost_defensive: tuple[int | float | str, int | float | str]
    possession_lost_midfield: tuple[int | float | str, int | float | str]
    duels: tuple[int | float | str, int | float | str]
    duels_accuracy: tuple[int | float | str, int | float | str]
    aerial_duels: tuple[int | float | str, int | float | str]
    aerial_duels_accuracy: tuple[int | float | str, int | float | str]
    dribbles_success: tuple[int | float | str, int | float | str]
    fouls_won: tuple[int | float | str, int | float | str]
    offsides: tuple[int | float | str, int | float | str]
    corners_won: tuple[int | float | str, int | float | str]

    class Settings:
        name = "match_general_stats"
        validate_on_save = True
        indexes = ["time_in_match"]


class MatchAttackStats(Document):
    time_in_match: Indexed(str)
    timestamp: datetime = Field(
        ..., description="Server timestamp when data was recorded"
    )  # NEW

    goals: tuple[int | float | str, int | float | str]
    shots: tuple[int | float | str, int | float | str]
    shots_on_target: tuple[int | float | str, int | float | str]
    shots_blocked: tuple[int | float | str, int | float | str]
    shots_headed: tuple[int | float | str, int | float | str]
    shots_outside_box: tuple[int | float | str, int | float | str]
    shots_inside_box: tuple[int | float | str, int | float | str]
    shots_accuracy_excluding_blocked_shots: tuple[int | float | str, int | float | str]
    shots_accuracy: tuple[int | float | str, int | float | str]
    key_passes: tuple[int | float | str, int | float | str]

    class Settings:
        name = "match_attack_stats"
        validate_on_save = True
        indexes = ["time_in_match"]


class MatchDefenceStats(Document):
    time_in_match: Indexed(str)
    timestamp: datetime = Field(
        ..., description="Server timestamp when data was recorded"
    )  # NEW

    tackles: tuple[int | float | str, int | float | str]
    tackles_accuracy: tuple[int | float | str, int | float | str]
    clearances: tuple[int | float | str, int | float | str]
    interceptions: tuple[int | float | str, int | float | str]
    ball_recoveries: tuple[int | float | str, int | float | str]
    ball_recoveries_attacking: tuple[int | float | str, int | float | str]
    ball_recoveries_defensive: tuple[int | float | str, int | float | str]
    ball_recoveries_midfield: tuple[int | float | str, int | float | str]
    ball_recoveries_attacking_accuracy: tuple[int | float | str, int | float | str]

    class Settings:
        name = "match_defence_stats"
        validate_on_save = True
        indexes = ["time_in_match"]


class MatchDisciplineStats(Document):
    time_in_match: Indexed(str)
    timestamp: datetime = Field(
        ..., description="Server timestamp when data was recorded"
    )  # NEW

    fouls_conceded: tuple[int | float | str, int | float | str]
    cards_yellow: tuple[int | float | str, int | float | str]
    cards_red: tuple[int | float | str, int | float | str]

    class Settings:
        name = "match_discipline_stats"
        validate_on_save = True
        indexes = ["time_in_match"]


class MatchDistributionStats(Document):
    time_in_match: str
    timestamp: datetime = Field(
        ..., description="Server timestamp when data was recorded"
    )  # NEW

    passes: tuple[int | float | str, int | float | str]
    passes_long: tuple[int | float | str, int | float | str]
    passes_long_proportion: tuple[int | float | str, int | float | str]
    passes_accuracy: tuple[int | float | str, int | float | str]
    passes_opponents_half: tuple[int | float | str, int | float | str]
    passes_opponents_half_accuracy: tuple[int | float | str, int | float | str]
    passes_final_third: tuple[int | float | str, int | float | str]
    passes_final_third_accuracy: tuple[int | float | str, int | float | str]
    passes_forward: tuple[int | float | str, int | float | str]
    passes_forward_accuracy: tuple[int | float | str, int | float | str]
    through_balls: tuple[int | float | str, int | float | str]
    final_thirds_entries: tuple[int | float | str, int | float | str]
    penalty_area_entries: tuple[int | float | str, int | float | str]
    open_play_crosses: tuple[int | float | str, int | float | str]
    crosses: tuple[int | float | str, int | float | str]
    crosses_accuracy: tuple[int | float | str, int | float | str]

    class Settings:
        name = "match_distribution_stats"
        validate_on_save = True
        indexes = ["time_in_match"]


# Export list
DocumentModels = [
    ClubsMetadata,
    PlayersMetadata,
    MatchesMetadata,
    MatchGeneralStats,
    MatchAttackStats,
    MatchDefenceStats,
    MatchDisciplineStats,
    MatchDistributionStats,
]
