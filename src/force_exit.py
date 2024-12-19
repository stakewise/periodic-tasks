import asyncio
import logging
import sys

from src.common.logs import setup_gql_log_level
from src.exit.tasks import force_exits

logger = logging.getLogger(__name__)


async def main() -> None:
    await force_exits()


try:
    setup_gql_log_level()
    asyncio.run(main())
except Exception as e:
    logger.exception(e)
    sys.exit(1)
