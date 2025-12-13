from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import websockets
from api.router import matches, missions, momentum, users
from clients import Clients
from configs import get_logger, redis_config

REDIS_DB_URL = f"redis://{redis_config.host}:{redis_config.port}/0"

mongo_client = Clients.get_mongo_client()
logger = get_logger(__name__)




@asynccontextmanager
async def lifespan(app: FastAPI):
    await mongo_client.initialize()
    try:
        app.state.redis = redis.from_url(REDIS_DB_URL, encoding="utf-8", decode_responses=True)
        pong = await app.state.redis.ping()
        logger.info(f"Connected to Redis: {pong}")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise e
    yield

    if hasattr(app.state, "redis"):
        await app.state.redis.close()
        logger.info("Closed Redis connection")
    await mongo_client.close()

app = FastAPI(title="Futstar App API", version="1.0.0", description="API for Futstar application", lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(matches.router)
app.include_router(users.router)
app.include_router(momentum.router)
app.include_router(websockets.router)
app.include_router(missions.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)