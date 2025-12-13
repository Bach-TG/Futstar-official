from datetime import datetime
from typing import Literal

from pydantic import BaseModel, model_validator


class MomentumIndex(BaseModel):
    time_in_match: str  # e.g., "45:00"
    momentum_value: float  # e.g., 0.75 representing 75% momentum
    home_goals: int | None = 0
    away_goals: int | None = 0


class MomentumPositions(BaseModel):
    position_id: str
    type: Literal['Long', 'Short']
    duration: Literal["30s", "1m", "2m", "3m", "5m", "10m"] 
    entry_value: float
    closed_value: float | None = None
    pnl_percentage: float
    amount: float
    timestamp: datetime
    user_id: str
    match_id: str
    time_in_match_entry: str
    time_in_match_closed: str | None = None
    status: Literal["Open", "Closed"] = "Closed"
    bonus_points_rewarded: float | None = 0
    home_team: str | None = None
    away_team: str | None = None
    competition: str | None = None


class PositionPnlUpdate(BaseModel):
    position_id: str
    pnl_percentage: float | str
    pnl_payout: float
    remaining_time: int  # in seconds
    current_value: float
    entry_value: float
    entry_time: str
    current_time: str
    current_bonus_points_reward: float | None = 0

    # @model_validator(mode="after")
    # def format_fields(cls, model):
    #     model.pnl_percentage = f"{model.pnl_percentage:.2f}%"
    #     return model