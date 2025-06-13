import asyncio
import logging

from periodic_tasks.common.clients import hot_wallet_account, setup_execution_client
from periodic_tasks.common.logs import setup_logging
from periodic_tasks.common.sentry import setup_sentry
from periodic_tasks.common.settings import NETWORK
from periodic_tasks.price.clients import sender_execution_client
from periodic_tasks.price.settings import SUPPORTED_NETWORKS
from periodic_tasks.price.tasks import check_and_sync

logger = logging.getLogger(__name__)


async def main() -> None:
    if NETWORK not in SUPPORTED_NETWORKS:
        raise ValueError(f'Price update in network {NETWORK} is not supported')

    if not hot_wallet_account:
        raise ValueError('Set HOT_WALLET_PRIVATE_KEY environment variable')

    await setup_execution_client(sender_execution_client, hot_wallet_account)
    await check_and_sync()


setup_logging()
setup_sentry()
asyncio.run(main())
