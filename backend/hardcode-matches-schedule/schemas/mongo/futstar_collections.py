from datetime import datetime, timezone
from typing import Any, Literal
from uuid import UUID, uuid4

from beanie import Document, Link
from pydantic import BaseModel, Field


class MatchMetadataDB(Document):
    id: UUID = Field(default_factory=uuid4, description="Unique identifier for the match")
    status: Literal["Scheduled", "Live", "Ended", "Testing"] = Field(default="Scheduled", description="Status of the match (Scheduled, Live, Ended, Testing)")
    # match_id: int = Field(default=..., description="Unique match identifier from the data source")
    home_team: str = Field(default=..., description="Name of the home team")
    away_team: str = Field(default=..., description="Name of the away team")
    match_time: datetime | None = None
    competition: str = Field(default=..., description="Name of the competition or league")
    home_team_logo: str = Field(default=..., description="URL to the home team logo")
    away_team_logo: str = Field(default=..., description="URL to the away team logo")
    opta_url: str | None = Field(default=None, description="URL to the Opta data for the match")
    mongodb_name: str | None = Field(default=None, description="Name of the MongoDB database")

    class Settings:
        name = "match_metadata"  # Collection name in MongoDB
        validate_on_save = True



class UserMetadataDB(Document):
    id: UUID = Field(default_factory=uuid4, description="Unique identifier for the user match metadata")
    wallet_address: str | None = Field(default=None, description="User's wallet address")
    balance: float | None = Field(default=None, description="User's balance in the application")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of the metadata record")
    bonus_points: float | None = Field(default=0, description="Bonus points awarded to the user")
    telegram_handle: str | None = Field(default=None, description="User's Telegram handle")
    user_level: int | None = Field(default=1, description="User's level in the application")
    experience_points: int | None = Field(default=0, description="User's experience points in the application")
    twitter_handle: str | None = Field(default=None, description="User's Twitter handle")
    telegram_connected: bool = Field(default=False, description="Indicates if the user has connected their Telegram account")
    twitter_connected: bool = Field(default=False, description="Indicates if the user has connected their Twitter account")
    discord_handle: str | None = Field(default=None, description="User's Discord handle")
    discord_connected: bool = Field(default=False, description="Indicates if the user has connected their Discord account")
    email: str | None = Field(default=None, description="User's email address")

    class Settings:
        name = "user_metadata"  # Collection name in MongoDB
        validate_on_save = True
        indexes = ["wallet_address", "id"]




class PositionHistoryDB(Document):
    id: UUID = Field(default_factory=uuid4, description="Unique identifier for the transaction history")
    type: Literal["Long", "Short"] = Field(default=..., description="Type of the transaction (Long or Short)")
    amount: float = Field(default=..., description="Amount of the transaction")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of the transaction")
    duration: Literal["30s", "1m", "2m", "3m", "5m", "10m"] = Field(default=..., description="Duration of the transaction")
    entry_value: float = Field(default=..., description="Entry price for the transaction")
    closed_value: float | None = Field(default=None, description="Closing price for the transaction")
    pnl_percentage: float = Field(default=..., description="Profit and Loss for the transaction in percentage")
    user_id: str = Field(default=..., description="Unique identifier for the user")
    match_id: str = Field(default=..., description="Unique identifier for the match")
    status: Literal["Open", "Closed"] = Field(default="Closed", description="Status of the position (Open or Closed)")
    time_in_match_entry: str = Field(default=..., description="Time in match when the position was entered")
    time_in_match_closed: str | None = Field(default=None, description="Time in match when the position was closed")
    bonus_points_rewarded: float | None = Field(default=0, description="Bonus points rewarded for this position")
    class Settings:
        name = "position_history"  # Collection name in MongoDB
        validate_on_save = True
        indexes = ["id"]


class MissionMetadataDB(Document):
    id: UUID = Field(default_factory=uuid4, description="Unique identifier for the mission metadata")
    mission_name: str = Field(default=..., description="Name of the mission")
    description: str = Field(default=..., description="Description of the mission")
    reward_points: float = Field(default=..., description="Reward points for completing the mission")
    is_active: bool = Field(default=True, description="Indicates if the mission is currently active")
    start_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Start date of the mission")
    end_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="End date of the mission")

    class Settings:
        name = "mission_metadata"  # Collection name in MongoDB
        validate_on_save = True


class UserMissionDB(Document):
    id: UUID = Field(default_factory=uuid4, description="Unique identifier for the user mission")
    user_id: str = Field(default=..., description="Unique identifier for the user")
    mission_id: UUID = Field(default=..., description="Unique identifier for the mission")
    progress_percentage: float = Field(default=0.0, description="Progress percentage of the mission")
    is_completed: bool = Field(default=False, description="Indicates if the mission is completed by the user")
    completion_date: datetime | None = Field(default=None, description="Date when the mission was completed")

    class Settings:
        name = "user_mission"  # Collection name in MongoDB
        validate_on_save = True
        indexes = ["user_id", "mission_id"]



DocumentModels = [MatchMetadataDB, UserMetadataDB, PositionHistoryDB, MissionMetadataDB, UserMissionDB]
    






