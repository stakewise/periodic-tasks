import logging

from eth_typing import ChecksumAddress
from web3 import Web3

from periodic_tasks.common.graph import get_multiple_harvest_params
from periodic_tasks.common.networks import ZERO_CHECKSUM_ADDRESS
from periodic_tasks.common.settings import EXECUTION_TRANSACTION_TIMEOUT
from periodic_tasks.exit.contracts import keeper_contract, multicall_contract

from . import settings
from .clients import execution_client, graph_client
from .contracts import RewardSplitterContract
from .graph import graph_get_reward_splitters

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def process_reward_splitter() -> None:
    vaults = [Web3.to_checksum_address(v) for v in settings.VAULTS]
    block = await execution_client.eth.get_block('finalized')

    logger.info('Fetching reward splitters')
    reward_splitters = await graph_get_reward_splitters(block_number=block['number'], vaults=vaults)

    if not reward_splitters:
        logger.info('No reward splitters found for given vaults')
        return

    # Reward splitter contract is used to encode abi calls
    # Actual calls are made by multicall contract
    # It's okay to put zero address here, because we don't need to interact with the contract
    reward_splitter_contract = RewardSplitterContract(
        abi_path='abi/IRewardSplitter.json',
        address=ZERO_CHECKSUM_ADDRESS,
        client=execution_client,
    )

    vaults = [rs.vault for rs in reward_splitters]
    vault_to_can_harvest_map = await get_vault_to_can_harvest_map(vaults=vaults)

    vault_to_harvest_params_map = await get_multiple_harvest_params(
        graph_client=graph_client, vaults=vaults
    )

    calls = []
    for reward_splitter in reward_splitters:
        vault = reward_splitter.vault
        harvest_params = vault_to_harvest_params_map.get(vault)
        can_harvest = vault_to_can_harvest_map[vault]
        if can_harvest and harvest_params:
            calls.append(
                (
                    reward_splitter.address,
                    reward_splitter_contract.get_update_vault_state_call(
                        harvest_params=harvest_params
                    ),
                )
            )
        for shareholder in reward_splitter.shareholders:
            calls.append(
                (
                    reward_splitter.address,
                    reward_splitter_contract.get_enter_exit_queue_on_behalf_call(
                        rewards=None,  # exiting all rewards
                        address=shareholder.address,
                    ),
                )
            )

    if settings.DRY_RUN:
        tx = await multicall_contract.functions.aggregate(calls).call()
        return

    tx = await multicall_contract.functions.aggregate(calls).transact()

    tx_hash = Web3.to_hex(tx)
    logger.info('Waiting for transaction %s confirmation', tx_hash)
    tx_receipt = await execution_client.eth.wait_for_transaction_receipt(
        tx, timeout=EXECUTION_TRANSACTION_TIMEOUT
    )
    if not tx_receipt['status']:
        logger.error(
            'Failed to confirm reward splitter tx: %s',
            tx_hash,
        )


async def get_vault_to_can_harvest_map(
    vaults: list[ChecksumAddress],
) -> dict[ChecksumAddress, bool]:
    vault_to_can_harvest_map: dict[ChecksumAddress, bool] = {}
    for vault in vaults:
        can_harvest = await keeper_contract.can_harvest(vault)
        vault_to_can_harvest_map[vault] = can_harvest
    return vault_to_can_harvest_map
