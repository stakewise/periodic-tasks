import asyncio
import logging

from periodic_tasks.common.clients import (
    execution_client,
    hot_wallet_account,
    setup_execution_client,
)
from periodic_tasks.common.graph_client import graph_client
from periodic_tasks.common.logs import setup_logging
from periodic_tasks.common.sentry import setup_sentry
from periodic_tasks.common.startup_checks import (
    wait_for_graph_node_sync_to_finalized_block,
)
from periodic_tasks.meta_vault.tasks import process_meta_vaults

logger = logging.getLogger(__name__)


async def main() -> None:
    if not hot_wallet_account:
        raise ValueError('Set HOT_WALLET_PRIVATE_KEY environment variable')

    await setup_execution_client(execution_client, hot_wallet_account)

    await wait_for_graph_node_sync_to_finalized_block(
        graph_client=graph_client,
        execution_client=execution_client,
    )

    await process_meta_vaults()


setup_logging()
setup_sentry()
asyncio.run(main())
