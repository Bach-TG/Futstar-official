from beanie import Document
from pydantic import Field


class MatchDataCollection(Document):
    match_id: str = Field(default=..., description="Unique identifier for the match")
    url: str | None = Field(default=None, description="URL of the match data source")

    class Settings:
        name = "match_data"  # Collection name in MongoDB
        validate_on_save = True

MatchDocumentModels = [MatchDataCollection]