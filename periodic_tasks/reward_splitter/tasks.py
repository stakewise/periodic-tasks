import logging

from eth_typing import ChecksumAddress, HexStr
from web3 import Web3

from periodic_tasks.common.graph import get_multiple_harvest_params
from periodic_tasks.common.networks import ZERO_CHECKSUM_ADDRESS
from periodic_tasks.common.settings import EXECUTION_TRANSACTION_TIMEOUT
from periodic_tasks.exit.contracts import keeper_contract, multicall_contract

from . import settings
from .clients import execution_client, graph_client
from .contracts import RewardSplitterContract
from .graph import graph_get_claimable_exit_requests, graph_get_reward_splitters

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
    reward_splitter_encoder = reward_splitter_contract.encoder()

    vaults = [rs.vault for rs in reward_splitters]
    vault_to_can_harvest_map = await get_vault_to_can_harvest_map(vaults=vaults)

    vault_to_harvest_params_map = await get_multiple_harvest_params(
        graph_client=graph_client, vaults=vaults
    )

    splitter_to_exit_requests = await graph_get_claimable_exit_requests(
        block_number=block['number'], reward_splitters=[rs.address for rs in reward_splitters]
    )

    # Multicall contract calls
    calls: list[tuple[ChecksumAddress, HexStr]] = []

    for reward_splitter in reward_splitters:
        logger.info(
            'Processing reward splitter %s for vault %s',
            reward_splitter.address,
            reward_splitter.vault,
        )

        vault = reward_splitter.vault
        harvest_params = vault_to_harvest_params_map.get(vault)

        can_harvest = vault_to_can_harvest_map[vault]
        logger.info('can_harvest %s, ', can_harvest)

        reward_splitter_calls: list[HexStr] = []

        if can_harvest and harvest_params:
            reward_splitter_calls.append(
                reward_splitter_encoder.update_vault_state(harvest_params=harvest_params)
            )

        for shareholder in reward_splitter.shareholders:
            logger.info('Processing shareholder %s', shareholder.address)
            reward_splitter_calls.append(
                reward_splitter_encoder.enter_exit_queue_on_behalf(
                    rewards=None,  # exiting all rewards
                    address=shareholder.address,
                )
            )

        exit_requests = splitter_to_exit_requests.get(reward_splitter.address, [])  # nosec
        for exit_request in exit_requests:
            logger.info(
                'Processing exit request with position ticket %s', exit_request.position_ticket
            )
            if exit_request.exit_queue_index is None:
                logger.info(
                    'Exit request with position ticket %s has no exit queue index',
                    exit_request.position_ticket,
                )
                continue
            reward_splitter_calls.append(
                reward_splitter_encoder.claim_exited_assets_on_behalf(
                    position_ticket=exit_request.position_ticket,
                    timestamp=exit_request.timestamp,
                    exit_queue_index=exit_request.exit_queue_index,
                ),
            )

        calls.extend([(reward_splitter.address, call) for call in reward_splitter_calls])

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
