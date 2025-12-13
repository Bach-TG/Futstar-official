from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ApiResponse(BaseModel):
    success: bool
    status_code: int
    message: str | None = None
    data: dict[str, Any] | None = None


class UserClaimedSuccessResponse(BaseModel):
    user_id: str
    mission_id: str
    claimed_at: datetime   # ISO 8601 format
    reward_points: int