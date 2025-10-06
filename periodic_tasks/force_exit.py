import asyncio
import logging

import periodic_tasks
from periodic_tasks.common.clients import (
    execution_client,
    hot_wallet_account,
    setup_execution_client,
)
from periodic_tasks.common.graph_client import graph_client
from periodic_tasks.common.logs import setup_logging
from periodic_tasks.common.sentry import setup_sentry
from periodic_tasks.common.settings import NETWORK
from periodic_tasks.common.startup_checks import (
    wait_for_graph_node_sync_to_finalized_block,
)
from periodic_tasks.exit.settings import SUPPORTED_NETWORKS
from periodic_tasks.exit.tasks import force_exits

logger = logging.getLogger(__name__)


async def main() -> None:
    logger.info('Starting periodic tasks %s', periodic_tasks.__version__)

    if NETWORK not in SUPPORTED_NETWORKS:
        raise ValueError(f'Force exits in network {NETWORK} is not supported')

    if not hot_wallet_account:
        raise ValueError('Set HOT_WALLET_PRIVATE_KEY environment variable')

    await setup_execution_client(execution_client, hot_wallet_account)

    await wait_for_graph_node_sync_to_finalized_block(
        graph_client=graph_client,
        execution_client=execution_client,
    )

    await force_exits()


setup_logging()
setup_sentry()
asyncio.run(main())
