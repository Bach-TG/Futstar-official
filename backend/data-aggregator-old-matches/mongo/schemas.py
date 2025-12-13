from datetime import datetime, timezone
from uuid import UUID

from beanie import Document, Indexed, Link
from pydantic import BaseModel, Field


class League(BaseModel):
    id: str = Field(..., description="ID of the league in Transfermarkt")
    name: str = Field(..., description="Name of the league")
    countryName: str = Field(..., description="Country name of the league")


class ClubsMetadata(Document):
    id: UUID
    club_id: str = Field(..., description="ID of the club in Transfermarkt")
    name: str = Field(..., description="Name of the club")
    league: League = Field(..., description="League information of the club")
    updated_at: datetime = Field(
        description="Timestamp of the last update to this record",
    )

    class Settings:
        name = "clubs_metadata"
        validate_on_save = True



class PlayersMetadata(Document):
    id: UUID
    player_id: str = Field(..., description="ID of the player in Transfermarkt")
    name: str = Field(..., description="Name of the player")
    age: int | None = Field(..., description="Age of the player")
    height: int | None = Field(..., description="Height of the player")
    nationality: str | None = Field(..., description="Nationality of the player")
    position: str | None = Field(..., description="Position information of the player")
    foot: str | None = Field(..., description="Preferred foot of the player")
    club: Link[ClubsMetadata] = Field(..., description="Reference to the player's club")
    club_id: str = Field(..., description="ID of the club in Transfermarkt")
    updated_at: datetime = Field(
        description="Timestamp of the last update to this record",
    )

    class Settings:
        name = "players_metadata"
        validate_on_save = True



class MatchesMetadata(Document):
    id: UUID
    match_id: str = Field(..., description="ID of the match in Transfermarkt")
    date: datetime = Field(..., description="Date and time of the match")
    status: str = Field(..., description="Status of the match")
    home_team: Link[ClubsMetadata] = Field(
        ..., description="Reference to the home team"
    )
    away_team: Link[ClubsMetadata] = Field(
        ..., description="Reference to the away team"
    )
    home_score: int | None = Field(..., description="Score of the home team")
    away_score: int | None = Field(..., description="Score of the away team")
    competition: str = Field(..., description="Competition information of the match")
    updated_at: datetime = Field(
        description="Timestamp of the last update to this record",
    )

    class Settings:
        name = "matches_metadata"
        validate_on_save = True


class MatchGeneralStats(Document):
    time_in_match: Indexed(str) = Field(..., description="Time in match for the statistics")
    possession: tuple[int | float | str, int | float | str] = Field(
        ..., description="Possession statistics as a tuple (home, away)"
    )
    possession_lost_defensive: tuple[int | float | str, int | float | str] = Field(
        ..., description="Possession lost in defensive third as a tuple (home, away)"
    )
    possession_lost_midfield: tuple[int | float | str, int | float | str] = Field(
        ..., description="Possession lost in midfield as a tuple (home, away)"
    )
    duels: tuple[int | float | str, int | float | str] = Field(
        ..., description="Duels statistics as a tuple (home, away)"
    )
    duels_accuracy: tuple[int | float | str, int | float | str] = Field(
        ..., description="Duels accuracy as a tuple (home, away)"
    )
    aerial_duels: tuple[int | float | str, int | float | str] = Field(
        ..., description="Aerial duels statistics as a tuple (home, away)"
    )
    aerial_duels_accuracy: tuple[int | float | str, int | float | str] = Field(
        ..., description="Aerial duels accuracy as a tuple (home, away)"
    )
    dribbles_success: tuple[int | float | str, int | float | str] = Field(
        ..., description="Successful dribbles as a tuple (home, away)"
    )
    fouls_won: tuple[int | float | str, int | float | str] = Field(
        ..., description="Fouls won as a tuple (home, away)"
    )
    offsides: tuple[int | float | str, int | float | str] = Field(
        ..., description="Offsides statistics as a tuple (home, away)"
    )
    corners_won: tuple[int | float | str, int | float | str] = Field(
        ..., description="Corners won as a tuple (home, away)"
    )

    class Settings:
        name = "match_general_stats"
        validate_on_save = True
        indexes = [
            "time_in_match",
        ]

class MatchAttackStats(Document):
    time_in_match: Indexed(str) = Field(..., description="Time in match for the statistics")
    goals: tuple[int | float | str, int | float | str] = Field(
        ..., description="Goals scored as a tuple (home, away)"
    )
    shots: tuple[int | float | str, int | float | str] = Field(
        ..., description="Total shots as a tuple (home, away)"
    )
    shots_on_target: tuple[int | float | str, int | float | str] = Field(
        ..., description="Shots on target as a tuple (home, away)"
    )
    shots_blocked: tuple[int | float | str, int | float | str] = Field(
        ..., description="Blocked shots as a tuple (home, away)"
    )
    shots_headed: tuple[int | float | str, int | float | str] = Field(
        ..., description="Headed shots as a tuple (home, away)"
    )
    shots_outside_box: tuple[int | float | str, int | float | str] = Field(
        ..., description="Shots from outside the box as a tuple (home, away)"
    )
    shots_inside_box: tuple[int | float | str, int | float | str] = Field(
        ..., description="Shots from inside the box as a tuple (home, away)"
    )
    shots_accuracy_excluding_blocked_shots: tuple[int | float | str, int | float | str] = Field(
        ..., description="Shots accuracy excluding blocked shots as a tuple (home, away)"
    )
    shots_accuracy: tuple[int | float | str, int | float | str] = Field(
        ..., description="Overall shots accuracy as a tuple (home, away)"
    )
    key_passes: tuple[int | float | str, int | float | str] = Field(
        ..., description="Key passes as a tuple (home, away)"
    )

    class Settings:
        name = "match_attack_stats"
        validate_on_save = True
        indexes = [
            "time_in_match",
        ]

class MatchDefenceStats(Document):
    time_in_match: Indexed(str) = Field(..., description="Time in match for the statistics")
    tackles: tuple[int | float | str, int | float | str] = Field(
        ..., description="Tackles made as a tuple (home, away)"
    )
    tackles_accuracy: tuple[int | float | str, int | float | str] = Field(
        ..., description="Tackles accuracy as a tuple (home, away)"
    )
    clearances: tuple[int | float | str, int | float | str] = Field(
        ..., description="Clearances made as a tuple (home, away)"
    )
    interceptions: tuple[int | float | str, int | float | str] = Field(
        ..., description="Interceptions made as a tuple (home, away)"
    )
    ball_recoveries: tuple[int | float | str, int | float | str] = Field(
        ..., description="Ball recoveries as a tuple (home, away)"
    )
    ball_recoveries_attacking: tuple[int | float | str, int | float | str] = Field(
        ..., description="Ball recoveries in attacking third as a tuple (home, away)"
    )
    ball_recoveries_defensive: tuple[int | float | str, int | float | str] = Field(
        ..., description="Ball recoveries in defensive third as a tuple (home, away)"
    )
    ball_recoveries_midfield: tuple[int | float | str, int | float | str] = Field(
        ..., description="Ball recoveries in midfield as a tuple (home, away)"
    )
    ball_recoveries_attacking_accuracy: tuple[int | float | str, int | float | str] = Field(
        ..., description="Ball recoveries accuracy in attacking third as a tuple (home, away)"
    )

    class Settings:
        name = "match_defence_stats"
        validate_on_save = True
        indexes = [
            "time_in_match",
        ]


class MatchDisciplineStats(Document):
    time_in_match: Indexed(str) = Field(..., description="Time in match for the statistics")
    fouls_conceded: tuple[int | float | str, int | float | str] = Field(
        ..., description="Fouls conceded as a tuple (home, away)"
    )
    cards_yellow: tuple[int | float | str, int | float | str] = Field(
        ..., description="Yellow cards received as a tuple (home, away)"
    )
    cards_red: tuple[int | float | str, int | float | str] = Field(
        ..., description="Red cards received as a tuple (home, away)"
    )

    class Settings:
        name = "match_discipline_stats"
        validate_on_save = True
        indexes = [
            "time_in_match",
        ]


class MatchDistributionStats(Document):
    time_in_match: str = Field(..., description="Time in match for the statistics")
    passes: tuple[int | float | str, int | float | str] = Field(
        ..., description="Total passes as a tuple (home, away)"
    )
    passes_long: tuple[int | float | str, int | float | str] = Field(
        ..., description="Long passes as a tuple (home, away)"
    )
    passes_long_proportion: tuple[int | float | str, int | float | str] = Field(
        ..., description="Proportion of long passes as a tuple (home, away)"
    )
    passes_accuracy: tuple[int | float | str, int | float | str] = Field(
        ..., description="Passes accuracy as a tuple (home, away)"
    )
    passes_opponents_half: tuple[int | float | str, int | float | str] = Field(
        ..., description="Passes in opponent's half as a tuple (home, away)"
    )
    passes_opponents_half_accuracy: tuple[int | float | str, int | float | str] = Field(
        ..., description="Passes accuracy in opponent's half as a tuple (home, away)"
    )
    passes_final_third: tuple[int | float | str, int | float | str] = Field(
        ..., description="Passes in final third as a tuple (home, away)"
    )
    passes_final_third_accuracy: tuple[int | float | str, int | float | str] = Field(
        ..., description="Passes accuracy in final third as a tuple (home, away)"
    )
    passes_forward: tuple[int | float | str, int | float | str] = Field(
        ..., description="Forward passes as a tuple (home, away)"
    )
    passes_forward_accuracy: tuple[int | float | str, int | float | str] = Field(
        ..., description="Forward passes accuracy as a tuple (home, away)"
    )
    through_balls: tuple[int | float | str, int | float | str] = Field(
        ..., description="Through balls as a tuple (home, away)"
    )
    final_thirds_entries: tuple[int | float | str, int | float | str] = Field(
        ..., description="Entries into final third as a tuple (home, away)"
    )
    penalty_area_entries: tuple[int | float | str, int | float | str] = Field(
        ..., description="Entries into penalty area as a tuple (home, away)"
    )
    open_play_crosses: tuple[int | float | str, int | float | str] = Field(
        ..., description="Open play crosses as a tuple (home, away)"
    )
    crosses: tuple[int | float | str, int | float | str] = Field(
        ..., description="Total crosses as a tuple (home, away)"
    )
    crosses_accuracy: tuple[int | float | str, int | float | str] = Field(
        ..., description="Crosses accuracy as a tuple (home, away)"
    )


    class Settings:
        name = "match_distribution_stats"
        validate_on_save = True
        indexes = [
            "time_in_match",
        ]

DocumentModels = [ClubsMetadata, PlayersMetadata, MatchesMetadata, MatchGeneralStats, MatchAttackStats, MatchDefenceStats, MatchDisciplineStats, MatchDistributionStats]
