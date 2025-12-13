from datetime import datetime

from pydantic import BaseModel

from utils.enums import MissionType


class MissionMetadata(BaseModel):
    mission_id: str
    mission_name: str
    description: str
    reward_points: int
    type: MissionType
    is_active: bool
    expiration_date: datetime | None = None
    created_at: datetime
    number_of_steps: int = 1
    