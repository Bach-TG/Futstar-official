import asyncio
import signal
import sys

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from configs import get_logger
from engine.updating_status import update_match_status

logger = get_logger(__name__)


def create_scheduler() -> AsyncIOScheduler:
    """Create and configure the APScheduler instance."""
    scheduler = AsyncIOScheduler(
        job_defaults={
            "coalesce": True,  # Combine multiple pending executions into one
            "max_instances": 1,  # Only one instance of job running at a time
            "misfire_grace_time": 60,  # Allow 60 seconds grace period for misfired jobs
        }
    )

    # Schedule update_match_status to run every 5 minutes starting at minute 3
    # Pattern: 3, 8, 13, 18, 23, 28, 33, 38, 43, 48, 53, 58
    scheduler.add_job(
        update_match_status,
        trigger=CronTrigger(minute="3,8,13,18,23,28,33,38,43,48,53,58"),
        id="update_match_status",
        name="Update Match Status",
        replace_existing=True,
    )

    logger.info("Scheduler configured with update_match_status job (every 5 min, offset +3)")
    return scheduler


async def main():
    """Main entry point for the scheduler service."""
    logger.info("Starting Match Status Updater Service...")

    scheduler = create_scheduler()

    # Setup graceful shutdown
    loop = asyncio.get_event_loop()
    shutdown_event = asyncio.Event()

    def shutdown_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating shutdown...")
        shutdown_event.set()

    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)

    try:
        scheduler.start()
        logger.info("Scheduler started successfully. Waiting for jobs...")

        # Run initial update on startup (optional)
        logger.info("Running initial match status update...")
        await update_match_status()

        # Keep running until shutdown signal
        await shutdown_event.wait()

    except Exception as e:
        logger.error(f"Error in scheduler: {e}")
        sys.exit(1)
    finally:
        logger.info("Shutting down scheduler...")
        scheduler.shutdown(wait=True)
        logger.info("Scheduler shutdown complete.")


if __name__ == "__main__":
    asyncio.run(main())