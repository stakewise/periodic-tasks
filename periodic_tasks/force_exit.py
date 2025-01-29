import asyncio
import logging

from periodic_tasks.common.logs import setup_gql_log_level
from periodic_tasks.common.sentry import setup_sentry
from periodic_tasks.exit.tasks import force_exits

logger = logging.getLogger(__name__)


async def main() -> None:
    await force_exits()


setup_sentry()
setup_gql_log_level()
asyncio.run(main())
