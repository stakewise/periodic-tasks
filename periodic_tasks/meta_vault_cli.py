import asyncio
import logging

from periodic_tasks.common.clients import (
    execution_client,
    hot_wallet_account,
    setup_execution_client,
)
from periodic_tasks.common.logs import setup_logging
from periodic_tasks.common.sentry import setup_sentry
from periodic_tasks.meta_vault.tasks import process_meta_vaults

logger = logging.getLogger(__name__)


async def main() -> None:
    if not hot_wallet_account:
        raise ValueError('Set HOT_WALLET_PRIVATE_KEY environment variable')

    await setup_execution_client(execution_client, hot_wallet_account)

    await process_meta_vaults()


setup_logging()
setup_sentry()
asyncio.run(main())
