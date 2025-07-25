import logging
from typing import cast

from eth_typing import ChecksumAddress, HexStr
from hexbytes import HexBytes
from web3 import Web3
from web3.types import Wei

from periodic_tasks.common.contracts import multicall_contract
from periodic_tasks.common.graph import graph_get_vaults
from periodic_tasks.common.networks import ZERO_CHECKSUM_ADDRESS
from periodic_tasks.common.settings import EXECUTION_TRANSACTION_TIMEOUT
from periodic_tasks.common.typings import HarvestParams
from periodic_tasks.common.utils import to_chunks
from periodic_tasks.exit.typings import ExitRequest
from periodic_tasks.reward_splitter.typings import RewardSplitter

from . import settings
from .clients import execution_client, graph_client
from .contracts import RewardSplitterContract, RewardSplitterEncoder
from .graph import graph_get_claimable_exit_requests, graph_get_reward_splitters

logger = logging.getLogger(__name__)


async def process_reward_splitters() -> None:
    """
    Processes reward splitters for the vaults specified in settings.

    This function performs the following steps:
    1. Fetches the list of vaults from Subgraph.
    2. Retrieves reward splitters associated with the vaults from Subgraph.
    3. Maps the vaults to their harvest params.
    4. Retrieves claimable exit requests for the reward splitters.
    5. Generates multicall contract calls for each reward splitter.
    6. Processes the multicall batches and waits for transaction confirmations.

    Raises:
        RuntimeError: If a transaction fails to confirm.
    """
    vaults = [Web3.to_checksum_address(v) for v in settings.VAULTS]
    block = await execution_client.eth.get_block('finalized')

    logger.info('Fetching reward splitters')
    reward_splitters = await graph_get_reward_splitters(block_number=block['number'], vaults=vaults)

    if not reward_splitters:
        logger.info('No reward splitters found for given vaults')
        return

    vaults = [rs.vault for rs in reward_splitters]

    graph_vaults_map = await graph_get_vaults(graph_client=graph_client, vaults=vaults)

    splitter_to_exit_requests = await graph_get_claimable_exit_requests(
        block_number=block['number'], receivers=[rs.address for rs in reward_splitters]
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

        graph_vault = graph_vaults_map[vault]
        can_harvest = graph_vault.can_harvest
        harvest_params = graph_vault.harvest_params
        exit_requests = splitter_to_exit_requests.get(reward_splitter.address, [])  # nosec

        reward_splitter_calls = await _get_reward_splitter_calls(
            reward_splitter=reward_splitter,
            can_harvest=can_harvest,
            harvest_params=harvest_params,
            exit_requests=exit_requests,
        )

        # Add up to multicall format calls
        calls.extend([(reward_splitter.address, call) for call in reward_splitter_calls])

    if not calls:
        logger.warning('No calls to process')
        return

    for calls_batch in to_chunks(calls, settings.MULTICALL_BATCH_SIZE):
        logger.info('Processing multicall batch')
        tx = await _multicall(calls_batch)

        if settings.DRY_RUN:
            continue

        tx = cast(HexBytes, tx)
        tx_hash = Web3.to_hex(tx)
        logger.info('Waiting for transaction %s confirmation', tx_hash)

        tx_receipt = await execution_client.eth.wait_for_transaction_receipt(
            tx, timeout=EXECUTION_TRANSACTION_TIMEOUT
        )
        if not tx_receipt['status']:
            raise RuntimeError(
                f'Failed to confirm reward splitter tx: {tx_hash}',
            )
        logger.info('Transaction %s confirmed', tx_hash)

    logger.info('All multicall batches processed')


async def _get_reward_splitter_calls(
    reward_splitter: RewardSplitter,
    can_harvest: bool,
    harvest_params: HarvestParams | None,
    exit_requests: list[ExitRequest],
) -> list[HexStr]:
    """
    Generate ABI encoded calls for the reward splitter contract.

    It includes calls:
    1. for updating the vault state,
    2. entering the exit queue on behalf of shareholders,
    3. claiming exited assets on behalf of shareholders.

    Returns:
        list[HexStr]: A list of ABI encoded calls for the reward splitter contract.
    """
    # ABI encoded calls without contract address
    reward_splitter_calls: list[HexStr] = []
    reward_splitter_encoder = _get_reward_splitter_encoder()

    reward_splitter_assets = await _get_reward_splitter_assets(reward_splitter)

    if reward_splitter_assets < settings.REWARD_SPLITTER_MIN_ASSETS:
        logger.info('Reward splitter %s has not enough assets to withdraw', reward_splitter.address)
    else:
        # Append update state call
        if can_harvest and harvest_params:
            reward_splitter_calls.append(
                reward_splitter_encoder.update_vault_state(harvest_params=harvest_params)
            )

        # Append enter exit queue on behalf calls
        for shareholder in reward_splitter.shareholders:
            logger.info('Processing shareholder %s', shareholder.address)

            reward_splitter_calls.append(
                reward_splitter_encoder.enter_exit_queue_on_behalf(
                    rewards=None,  # exiting all rewards
                    address=shareholder.address,
                )
            )

    # Append claim exited assets on behalf calls
    if not exit_requests:
        logger.info('No exit requests for reward splitter %s', reward_splitter.address)

    for exit_request in exit_requests:
        logger.info('Processing exit request with position ticket %s', exit_request.position_ticket)
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

    return reward_splitter_calls


async def _get_reward_splitter_assets(reward_splitter: RewardSplitter) -> Wei:
    return Wei(sum(sh.earned_vault_assets for sh in reward_splitter.shareholders))


async def _multicall(calls: list[tuple[ChecksumAddress, HexStr]]) -> HexBytes | None:
    """
    Helper function to execute multicall:
    - Calls the original contract if all calls are to the same address.
    - Calls multicall contract otherwise.
    - Simulates the transaction if DRY_RUN is enabled.
    - Sends the transaction otherwise.
    """
    if not calls:
        return None

    distinct_addresses = list(set(address for address, _ in calls))
    if len(distinct_addresses) == 1:
        # Call the original contract when possible
        # as it makes it easier to find the transaction in the block explorer on the contract page
        contract = RewardSplitterContract(
            abi_path='abi/IRewardSplitter.json',
            address=distinct_addresses[0],
            client=execution_client,
        )
        contract_func = contract.functions.multicall([call for _, call in calls])
    else:
        # Call multicall contract
        contract_func = multicall_contract.functions.aggregate(calls)

    # Simulate transaction if DRY_RUN is enabled
    if settings.DRY_RUN:
        await contract_func.call()
        logger.info('Simulated multicall transaction')
        return None

    # Send transaction
    tx = await contract_func.transact()
    return tx


def _get_reward_splitter_encoder() -> RewardSplitterEncoder:
    # Reward splitter contract is used to encode abi calls.
    # Not for sending transactions.
    # It's okay to put zero address here.
    reward_splitter_contract = RewardSplitterContract(
        abi_path='abi/IRewardSplitter.json',
        address=ZERO_CHECKSUM_ADDRESS,
        client=execution_client,
    )
    return reward_splitter_contract.encoder()
