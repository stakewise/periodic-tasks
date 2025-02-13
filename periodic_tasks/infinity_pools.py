import asyncio
import logging

from periodic_tasks.common.logs import setup_gql_log_level
from periodic_tasks.common.sentry import setup_sentry
from periodic_tasks.pools.tasks import handle_pools

logger = logging.getLogger(__name__)


async def main() -> None:
    await handle_pools()


setup_sentry()
setup_gql_log_level()
asyncio.run(main())
