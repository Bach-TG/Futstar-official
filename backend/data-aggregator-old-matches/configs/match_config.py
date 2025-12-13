from pydantic import BaseModel


class MatchConfig(BaseModel):
    home_team: str
    away_team: str
    url: str