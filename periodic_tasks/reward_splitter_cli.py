import asyncio
import logging

from periodic_tasks.common.clients import hot_wallet_account, setup_execution_client
from periodic_tasks.common.logs import setup_logging
from periodic_tasks.common.sentry import setup_sentry
from periodic_tasks.reward_splitter.clients import execution_client
from periodic_tasks.reward_splitter.settings import DRY_RUN
from periodic_tasks.reward_splitter.tasks import process_reward_splitters

logger = logging.getLogger(__name__)


async def main() -> None:
    if not hot_wallet_account:
        raise ValueError('Set HOT_WALLET_PRIVATE_KEY environment variable')
    await setup_execution_client(execution_client, hot_wallet_account)

    await process_reward_splitters()


setup_logging()
setup_sentry()

if DRY_RUN:
    logger.info('Dry run mode is enabled')

asyncio.run(main())
