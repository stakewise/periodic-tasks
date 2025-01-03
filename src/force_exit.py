import asyncio
import logging

from src.common.logs import setup_gql_log_level
from src.common.sentry import setup_sentry
from src.exit.tasks import force_exits

logger = logging.getLogger(__name__)


async def main() -> None:
    await force_exits()


setup_sentry()
setup_gql_log_level()
asyncio.run(main())
