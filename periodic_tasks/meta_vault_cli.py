import asyncio
import logging

from periodic_tasks.common.clients import (
    execution_client,
    hot_wallet_account,
    setup_execution_client,
)
from periodic_tasks.common.logs import setup_logging
from periodic_tasks.common.sentry import setup_sentry
from periodic_tasks.meta_vault.tasks import process_all_meta_vaults

logger = logging.getLogger(__name__)


async def main() -> None:
    if not hot_wallet_account:
        raise ValueError('Set HOT_WALLET_PRIVATE_KEY environment variable')

    logger.info('Wallet address: %s', hot_wallet_account.address)

    await setup_execution_client(execution_client, hot_wallet_account)

    block = await execution_client.eth.get_block('finalized')
    await process_all_meta_vaults(block_number=block['number'])


setup_logging()
setup_sentry()
asyncio.run(main())
