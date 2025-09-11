import asyncio
import logging
from typing import cast

from eth_typing import BlockIdentifier, BlockNumber
from sw_utils.graph.client import GraphClient
from web3 import AsyncWeb3

from periodic_tasks.common.graph import graph_get_latest_block

logger = logging.getLogger(__name__)


async def wait_for_graph_node_sync_to_finalized_block(
    graph_client: GraphClient, execution_client: AsyncWeb3
) -> None:
    """
    Waits until graph node is available and synced to the finalized block of execution node.
    """
    await _wait_for_graph_node_sync(
        graph_client=graph_client,
        execution_client=execution_client,
        block_identifier='finalized',
        sleep_interval=10,
    )


async def wait_for_graph_node_sync_to_block(
    graph_client: GraphClient, block_number: BlockNumber
) -> None:
    """
    Waits until graph node is available and synced to the specified block number of execution node.
    Useful for checking against latest block.
    """
    await _wait_for_graph_node_sync(
        graph_client=graph_client,
        execution_client=None,
        block_identifier=block_number,
        sleep_interval=3,
    )


async def _wait_for_graph_node_sync(
    graph_client: GraphClient,
    execution_client: AsyncWeb3 | None,
    block_identifier: BlockIdentifier,
    sleep_interval: int,
) -> None:
    """
    Waits until graph node is available and synced to the specified block of execution node.
    """

    while True:
        try:
            graph_block_number = await graph_get_latest_block(graph_client)
        except Exception as e:
            logger.warning(
                'The graph node located at %s is not available: %s',
                graph_client.endpoint,
                str(e),
            )
            await asyncio.sleep(sleep_interval)
            continue

        if isinstance(block_identifier, int):
            # Fixed block number
            execution_block_number = block_identifier
        else:
            # Example: block_identifier = 'finalized'
            # Block number is changing on each iteration,
            # so we need to fetch it from execution client
            execution_client = cast(AsyncWeb3, execution_client)
            execution_block_number = (await execution_client.eth.get_block(block_identifier))[
                'number'
            ]

        if graph_block_number >= execution_block_number:
            return

        logger.warning(
            'Waiting for the graph node located at %s to sync up to block %d.',
            graph_client.endpoint,
            execution_block_number,
        )
        await asyncio.sleep(sleep_interval)
