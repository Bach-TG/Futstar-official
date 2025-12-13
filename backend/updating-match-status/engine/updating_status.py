import aiohttp

from configs import futstar_backend_config, get_logger

logger = get_logger(__name__)

refresh_match_status_endpoint = (
    f"http://{futstar_backend_config.host}:{futstar_backend_config.port}/matches/refresh_matches_status"
)


async def update_match_status():
    """
    Call the backend API to refresh match statuses.
    Runs every 5 minutes at offset +3 (3, 8, 13, ..., 58).
    """
    logger.info(f"Calling endpoint: {refresh_match_status_endpoint}")

    try:
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(refresh_match_status_endpoint) as response:
                if response.status in (200, 204):
                    logger.info("Successfully updated match statuses.")
                else:
                    text = await response.text()
                    logger.error(
                        f"Failed to update match statuses. "
                        f"Status code: {response.status}, Response: {text}"
                    )
    except aiohttp.ClientError as e:
        logger.error(f"HTTP client error while updating match statuses: {e}")
    except Exception as e:
        logger.error(f"Exception occurred while updating match statuses: {e}")