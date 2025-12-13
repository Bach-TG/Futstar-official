from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from schemas.missions import MissionMetadata


class UserMetadata(BaseModel):
    user_id: str
    balance: float | None = None
    wallet_address: str | None = None
    telegram_handle: str | None = None
    bonus_points: float | None = 0
    user_level: int | None = 1
    experience_points: int | None = 0
    twitter_handle: str | None = None
    discord_handle: str | None = None
    email: str | None = None
    level_up_required_experience: int | None = None


class UserMissionProgress(BaseModel):
    user_id: str
    progress_percentage: float
    is_completed: bool
    completion_date: datetime | None = None
    last_updated: datetime
    is_claimed: bool
    mission: MissionMetadata
    number_of_steps_completed: int = 0




