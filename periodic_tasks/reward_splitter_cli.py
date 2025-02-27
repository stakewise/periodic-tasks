import asyncio
import logging

from periodic_tasks.common.logs import setup_gql_log_level
from periodic_tasks.reward_splitter.settings import DRY_RUN
from periodic_tasks.reward_splitter.tasks import process_reward_splitter

logging.basicConfig(level=logging.INFO)
setup_gql_log_level()

logger = logging.getLogger(__name__)


async def main() -> None:
    await process_reward_splitter()


if __name__ == '__main__':
    if DRY_RUN:
        logger.info('Dry run mode is enabled')

    asyncio.run(main())
