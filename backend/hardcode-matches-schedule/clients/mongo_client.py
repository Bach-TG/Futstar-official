from typing import Any

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from configs import get_logger, mongo_config
from schemas.mongo.futstar_collections import DocumentModels
from schemas.mongo.match_data_collection import MatchDocumentModels

logger = get_logger(__name__)


class MongoClient():
    def __init__(self, db_name: str = str(mongo_config.db_name)) -> None:
        self.client: AsyncIOMotorClient[Any] = AsyncIOMotorClient(
            f"{mongo_config.uri}",
            uuidRepresentation="standard",
        )
        self.database: str = db_name
        self.db: AsyncIOMotorDatabase[Any] = self.client[self.database]

    async def initialize(self):
        await init_beanie(
            self.db,
            document_models=DocumentModels if self.database == str(mongo_config.db_name) else MatchDocumentModels,
        )
        logger.info(f"MongoDB client initialized with database: {self.database}.")

    async def close(self):
        self.client.close()
        logger.info(f"MongoDB client closed for database: {self.database}.")
