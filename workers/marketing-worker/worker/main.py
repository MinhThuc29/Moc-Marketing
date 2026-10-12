import asyncio
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (worker): %(message)s"
)
logger = logging.getLogger("marketing-worker")


async def main():
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    logger.info("Mộc Healthy Marketing Worker started. Listening on %s...", redis_url)
    try:
        while True:
            await asyncio.sleep(10)
    except (asyncio.CancelledError, KeyboardInterrupt):
        logger.info("Marketing Worker shutting down...")


if __name__ == "__main__":
    asyncio.run(main())
