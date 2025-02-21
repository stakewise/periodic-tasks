import asyncio
import logging

from hexbytes import HexBytes
from sw_utils import GasManager
from web3 import AsyncWeb3
from web3.contract.async_contract import AsyncContractFunction
from web3.types import TxParams

from periodic_tasks.common.settings import (
    ATTEMPTS_WITH_DEFAULT_GAS,
    MAX_FEE_PER_GAS_GWEI,
    PRIORITY_FEE_NUM_BLOCKS,
    PRIORITY_FEE_PERCENTILE,
    network_config,
)

logger = logging.getLogger(__name__)


def build_gas_manager(execution_client: AsyncWeb3) -> GasManager:
    return GasManager(
        execution_client=execution_client,
        max_fee_per_gas_gwei=MAX_FEE_PER_GAS_GWEI,
        priority_fee_num_blocks=PRIORITY_FEE_NUM_BLOCKS,
        priority_fee_percentile=PRIORITY_FEE_PERCENTILE,
    )


async def transaction_gas_wrapper(
    client: AsyncWeb3, tx_function: AsyncContractFunction, tx_params: TxParams | None = None
) -> HexBytes:
    """Handles periods with high gas in the network."""
    if not tx_params:
        tx_params = {}
    gas_manager = build_gas_manager(client)

    # trying to submit with basic gas
    for i in range(ATTEMPTS_WITH_DEFAULT_GAS):
        try:
            return await tx_function.transact(tx_params)
        except ValueError as e:
            # Handle only FeeTooLow error
            code = None
            if e.args and isinstance(e.args[0], dict):
                code = e.args[0].get('code')
            if not code or code != -32010:
                raise e
            logger.exception(e)
            if i < ATTEMPTS_WITH_DEFAULT_GAS - 1:  # skip last sleep
                await asyncio.sleep(network_config.SECONDS_PER_BLOCK)

    # use high priority fee
    tx_params = tx_params | await gas_manager.get_high_priority_tx_params()
    return await tx_function.transact(tx_params)
