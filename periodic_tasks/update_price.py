import asyncio
import logging

from periodic_tasks.common.sentry import setup_sentry
from periodic_tasks.price.tasks import check_and_sync

logger = logging.getLogger(__name__)


async def main() -> None:
    await check_and_sync()


setup_sentry()
asyncio.run(main())
