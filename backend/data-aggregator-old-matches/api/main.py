from contextlib import asynccontextmanager

from fastapi import FastAPI

from clients import Clients

mongo_client = Clients.get_mongo_client()



@asynccontextmanager
async def lifespan(app: FastAPI):
    await mongo_client.initialize()
    yield
    await mongo_client.close()


app = FastAPI(
    title="Data Aggregator Old Matches API",
    description="API for aggregating old match data.",
    version="0.1.0",
)