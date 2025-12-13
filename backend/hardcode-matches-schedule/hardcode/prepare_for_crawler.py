from clients import Clients
from configs import get_logger
from schemas.mongo.match_data_collection import MatchDataCollection

logger = get_logger(__name__)


async def prepare_for_crawler(match_id: str, opta_url: str):

    data = {
        "match_id": match_id,
        "opta_url": opta_url,
    }
    match_id = data["match_id"]
    url = data["opta_url"]
    logger.info(f"Preparing match ID: {match_id} with URL: {url}")
    mongo_match_client = Clients.get_mongo_client(db_name=match_id)
    await mongo_match_client.initialize()
    match_data = MatchDataCollection(
        match_id=match_id,
        url=url,
    )

    try:
        await match_data.insert()
        logger.info(f"Inserted match data for match ID: {match_id}")
    except Exception as e:
        logger.error(f"Error inserting match data for match ID {match_id}: {e}")


if __name__ == "__main__":
    import asyncio
    match_id = input("Enter match name for crawler: ")
    opta_url = input("Enter Opta URL: ")
    asyncio.run(prepare_for_crawler(match_id, opta_url))
    logger.info(f"Preparation complete for match ID: {match_id}")