from typing import Any

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from configs import get_logger, mongo_config
from mongo.schemas import DocumentModels
from services.base_singleton import SingletonMeta

logger = get_logger(__name__)


class MongoClient(metaclass=SingletonMeta):
    def __init__(self):
        self.client: AsyncIOMotorClient[Any] = AsyncIOMotorClient(
            mongo_config.uri,
            uuidRepresentation="standard",
        )
        self.db: AsyncIOMotorDatabase[Any] = None

    async def initialize(self, db_name: str):
        """
        Re-init Beanie với DB tương ứng trận đấu.
        """
        self.db = self.client[db_name]

        await init_beanie(
            database=self.db,
            document_models=DocumentModels,
        )
        logger.info(f"MongoDB initialized for DB: {db_name}")

    async def close(self):
        self.client.close()
        logger.info("MongoDB client closed.")
