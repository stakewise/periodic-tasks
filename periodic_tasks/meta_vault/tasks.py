import logging

from eth_typing import ChecksumAddress, HexStr
from sw_utils import GNO_NETWORKS, convert_to_mgno
from web3 import Web3
from web3.types import BlockNumber

from periodic_tasks.common.clients import execution_client
from periodic_tasks.common.contracts import (
    VaultContract,
    get_vault_contract,
    keeper_contract,
    multicall_contract,
)
from periodic_tasks.common.execution import wait_for_tx_confirmation
from periodic_tasks.common.graph import graph_get_vaults
from periodic_tasks.common.graph_client import graph_client
from periodic_tasks.common.networks import ZERO_CHECKSUM_ADDRESS
from periodic_tasks.common.settings import NETWORK, network_config
from periodic_tasks.common.typings import Vault
from periodic_tasks.exit.graph import graph_get_exit_requests_for_meta_vault
from periodic_tasks.exit.typings import ExitRequest
from periodic_tasks.meta_vault.contracts import MetaVaultContract
from periodic_tasks.meta_vault.exceptions import ClaimDelayNotPassedException
from periodic_tasks.meta_vault.typings import ContractCall, SubVaultExitRequest

from . import settings

logger = logging.getLogger(__name__)


async def process_meta_vaults() -> None:
    meta_vaults_map = await graph_get_vaults(
        graph_client=graph_client,
        is_meta_vault=True,
    )

    vaults_updated_previously: set[ChecksumAddress] = set()

    for meta_vault_address in settings.META_VAULTS:
        logger.info('Processing meta vault: %s', meta_vault_address)

        root_meta_vault = meta_vaults_map.get(meta_vault_address)
        if not root_meta_vault:
            logger.error('Meta vault %s not found in subgraph', meta_vault_address)
            continue

        if not root_meta_vault.sub_vaults:
            logger.info('Meta vault %s has no sub vaults. Skipping.', meta_vault_address)
            continue

        # Update the state for the entire meta vault tree
        try:
            vaults_updated_in_tree = await meta_vault_tree_update_state(
                root_meta_vault=root_meta_vault,
                meta_vaults_map=meta_vaults_map,
                vaults_updated_previously=vaults_updated_previously,
            )
        except ClaimDelayNotPassedException as e:
            logger.error(
                'Can not process meta vault %s because claim delay for exit request with '
                'position ticket %s has not passed yet',
                root_meta_vault.address,
                e.exit_request.position_ticket,
            )
            continue

        vaults_updated_previously.update(vaults_updated_in_tree)

        # Deposit to sub vaults if there are withdrawable assets
        await process_deposit_to_sub_vaults(meta_vault_address=meta_vault_address)


async def meta_vault_tree_update_state(
    root_meta_vault: Vault,
    meta_vaults_map: dict[ChecksumAddress, Vault],
    vaults_updated_previously: set[ChecksumAddress],
) -> set[ChecksumAddress]:
    """
    Traverse the meta vault tree in bottom-up order and update the state for each meta vault.
    This ensures that sub vaults are updated before their parent meta vaults.
    """
    meta_vault_addresses = get_meta_vault_addresses_bottom_up(
        root_meta_vault=root_meta_vault,
        meta_vaults_map=meta_vaults_map,
    )
    # Copy the set to avoid modifying the original set
    vaults_updated = set()

    # Update each meta vault in bottom-up order
    for meta_vault_address in meta_vault_addresses:
        vaults_updated_in_vault = await meta_vault_update_state(
            meta_vault=meta_vaults_map[meta_vault_address],
            vaults_updated_previously=vaults_updated_previously,
        )
        vaults_updated.update(vaults_updated_in_vault)

    return vaults_updated


def get_meta_vault_addresses_bottom_up(
    root_meta_vault: Vault,
    meta_vaults_map: dict[ChecksumAddress, Vault],
) -> list[ChecksumAddress]:
    stack = [root_meta_vault.address]
    meta_vaults: list[ChecksumAddress] = []

    while stack:
        # Take the last meta vault
        meta_vault_address = stack.pop()
        meta_vault = meta_vaults_map[meta_vault_address]

        for sub_vault in meta_vault.sub_vaults:
            if sub_vault in meta_vaults_map:
                stack.append(sub_vault)

        meta_vaults.append(meta_vault.address)

    # Return in bottom-up order
    return meta_vaults[::-1]


async def meta_vault_update_state(
    meta_vault: Vault,
    vaults_updated_previously: set[ChecksumAddress],
) -> set[ChecksumAddress]:
    """
    Update the state for the root meta vault.
    Assuming all its meta sub vaults have already been updated.

    `vaults_updated_previously` is a set of vault addresses that have already been updated
    as a part of another meta vault tree. This is to avoid duplicate updates.
    Subgraph may not sync fast enough to reflect the state changes made by previous transactions,
    so we need to keep track of the vaults that have already been updated.

    Returns a set of vault addresses that were updated in this call.
    """
    calls_with_description = await _get_meta_vault_update_state_calls(
        meta_vault=meta_vault,
    )

    calls: list[tuple[ChecksumAddress, HexStr]] = []
    tx_steps: list[str] = []
    vaults_updated: set[ChecksumAddress] = set()

    # Filter out calls for vaults that have already been updated
    for c in calls_with_description:
        if c.address in vaults_updated_previously:
            logger.info(
                'Vault %s is already updated as a part of another meta vault tree',
                c.address,
            )
            continue
        calls.append((c.address, c.data))
        tx_steps.append(c.description)
        vaults_updated.add(c.address)

    if not calls:
        logger.info('Meta vault %s state is up-to-date, no updates needed', meta_vault.address)
        return set()

    # Submit the transaction
    logger.info(
        'Submitting transaction to update state for meta vault tree %s',
        meta_vault.address,
    )
    logger.info('Transaction steps: \n%s', '\n'.join(tx_steps))

    tx_hash = await multicall_contract.tx_aggregate(calls)

    logger.info('Waiting for transaction %s confirmation', tx_hash)
    await wait_for_tx_confirmation(execution_client, tx_hash)
    logger.info('Transaction %s confirmed', tx_hash)

    return vaults_updated


async def _get_meta_vault_update_state_calls(
    meta_vault: Vault,
) -> list[ContractCall]:
    """
    Get state update calls for a single meta vault and its sub vaults.
    Skips meta vaults among sub vaults.
    Each call is a tuple of (vault_address, call_data, description).
    """
    logger.info('Getting state update calls for meta vault %s', meta_vault.address)

    # Get sub vaults
    sub_vaults = await graph_get_vaults(
        graph_client=graph_client,
        vaults=meta_vault.sub_vaults,
    )
    sub_vaults_to_harvest: list[ChecksumAddress] = []
    calls: list[ContractCall] = []

    # Vault contract
    vault_encoder = VaultContract(
        abi_path='abi/IEthVault.json',
        address=ZERO_CHECKSUM_ADDRESS,
        client=execution_client,
    ).encoder()

    # Filter harvestable sub vaults and prepare calls for updating their state
    for sub_vault in sub_vaults.values():
        if not sub_vault.can_harvest:
            logger.info('Sub vault %s is not harvestable, skipping', sub_vault.address)
            continue

        # Handle nested meta vaults separately
        if sub_vault.is_meta_vault:
            logger.info('Sub vault %s is a meta vault, skipping', sub_vault.address)
            continue

        logger.info('Getting state update call for sub vault %s', sub_vault.address)
        sub_vaults_to_harvest.append(sub_vault.address)
        calls.append(
            ContractCall(
                address=sub_vault.address,
                data=vault_encoder.update_state(
                    sub_vault.harvest_params,
                ),
                description=f'Update state for sub vault {sub_vault.address}',
            )
        )

    # Meta vault contract
    meta_vault_contract = MetaVaultContract(
        abi_path='abi/IEthMetaVault.json',
        address=meta_vault.address,
        client=execution_client,
    )

    # Collect claimable exit requests for the sub vaults
    sub_vault_exit_requests = await get_claimable_sub_vault_exit_requests(
        meta_vault_contract=meta_vault_contract
    )
    meta_vault_encoder = meta_vault_contract.encoder()

    # Claim sub vaults exited assets
    if sub_vault_exit_requests:
        logger.info(
            'Meta vault %s has %d sub vault exit requests to claim',
            meta_vault.address,
            len(sub_vault_exit_requests),
        )
        calls.append(
            ContractCall(
                address=meta_vault.address,
                data=meta_vault_encoder.claim_sub_vaults_exited_assets(sub_vault_exit_requests),
                description=f'Claim {len(sub_vault_exit_requests)} sub vault exit requests '
                f'for meta vault {meta_vault.address}',
            )
        )
    else:
        logger.info('No sub vault exit requests to claim for meta vault %s', meta_vault.address)

    # Update meta vault state
    is_rewards_nonce_outdated = await is_meta_vault_rewards_nonce_outdated(
        meta_vault_contract=meta_vault_contract,
    )

    if sub_vaults_to_harvest or is_rewards_nonce_outdated:
        calls.append(
            ContractCall(
                address=meta_vault.address,
                data=meta_vault_encoder.update_state(meta_vault.harvest_params),
                description=f'Update state for meta vault {meta_vault.address}',
            ),
        )
    return calls


async def get_claimable_sub_vault_exit_requests(
    meta_vault_contract: MetaVaultContract,
) -> list[SubVaultExitRequest]:
    """
    Get claimable exit requests for the given sub vaults.
    """
    meta_vault_address = meta_vault_contract.address
    vault_to_exit_requests = await graph_get_exit_requests_for_meta_vault(
        meta_vault=meta_vault_address,
    )
    exit_requests: list[ExitRequest] = flatten_exit_requests(vault_to_exit_requests)
    ensure_claim_delay_passed(exit_requests)

    sub_vault_exit_requests = [
        SubVaultExitRequest.from_exit_request(exit_request) for exit_request in exit_requests
    ]

    await fix_exit_queue_indexes(sub_vault_exit_requests=sub_vault_exit_requests)
    return [r for r in sub_vault_exit_requests if r.has_exit_queue_index]


def flatten_exit_requests(
    vault_to_exit_requests: dict[ChecksumAddress, list[ExitRequest]],
) -> list[ExitRequest]:
    """
    Flatten a mapping from vault address to list of ExitRequest objects
    into a single list of ExitRequest objects.
    """
    res: list[ExitRequest] = []
    for exit_requests in vault_to_exit_requests.values():
        res.extend(exit_requests)
    return res


def ensure_claim_delay_passed(exit_requests: list[ExitRequest]) -> None:
    """
    Ensure that the claim delay has passed for all exit requests.
    Raises ClaimDelayNotPassedException if any exit request is still waiting for claim delay.
    """
    for exit_request in exit_requests:
        if exit_request.is_waiting_for_claim_delay:
            raise ClaimDelayNotPassedException(exit_request)


async def fix_exit_queue_indexes(sub_vault_exit_requests: list[SubVaultExitRequest]) -> None:
    """
    The exit queue index is updated by the Subgraph when sufficient funds are available
    to fulfill an exit request.
    Exit queue index may be null in the case when updateState just happened,
    and the Subgraph has not yet indexed the change.

    This function updates any sub vault exit requests that have
    a null exit queue index by fetching the correct value from the contract.
    """
    for sub_vault_exit_request in sub_vault_exit_requests:
        if sub_vault_exit_request.exit_queue_index is not None:
            continue
        sub_vault_contract = get_vault_contract(sub_vault_exit_request.vault)
        exit_queue_index = await sub_vault_contract.get_exit_queue_index(
            sub_vault_exit_request.position_ticket
        )
        if exit_queue_index == -1:
            continue
        logger.info(
            'Fixing exit queue index for vault %s position ticket %s',
            sub_vault_exit_request.vault,
            sub_vault_exit_request.position_ticket,
        )
        sub_vault_exit_request.exit_queue_index = exit_queue_index


async def is_meta_vault_rewards_nonce_outdated(
    meta_vault_contract: MetaVaultContract,
) -> bool:
    """
    Check if the meta vault rewards nonce is outdated compared to the keeper contract.
    We can't read the rewards nonce from meta vault directly
    because it is stored in private attribute.
    Solution: compare events.
    """
    current_block = await execution_client.eth.get_block_number()

    # Find the last rewards updated event in the Keeper contract
    keeper_event = await keeper_contract.get_last_rewards_updated_event(
        from_block=network_config.KEEPER_GENESIS_BLOCK, to_block=current_block
    )
    if keeper_event is None:
        logger.info('No RewardsUpdated event found in the Keeper contract')
        return False

    # Find the last rewards nonce updated event in the meta vault contract
    # since the last Keeper vote
    meta_vault_event = await meta_vault_contract.get_last_rewards_nonce_updated_event(
        from_block=BlockNumber(keeper_event['blockNumber'] + 1), to_block=current_block
    )

    # If no meta vault event is found, the rewards nonce is outdated
    return meta_vault_event is None


async def process_deposit_to_sub_vaults(meta_vault_address: ChecksumAddress) -> None:
    meta_vault_contract = MetaVaultContract(
        abi_path='abi/IEthMetaVault.json',
        address=meta_vault_address,
        client=execution_client,
    )
    withdrawable_assets = await meta_vault_contract.withdrawable_assets()

    if NETWORK in GNO_NETWORKS:
        withdrawable_assets = convert_to_mgno(withdrawable_assets)

    logger.info(
        'Meta vault %s has withdrawable assets: %.2f %s',
        meta_vault_address,
        Web3.from_wei(withdrawable_assets, 'ether'),
        network_config.VAULT_BALANCE_UNIT,
    )

    if withdrawable_assets < settings.META_VAULT_MIN_DEPOSIT_AMOUNT:
        return

    logger.info('Depositing to sub vaults for meta vault %s', meta_vault_address)
    tx_hash = await meta_vault_contract.deposit_to_sub_vaults()

    logger.info('Waiting for transaction %s confirmation', tx_hash)
    await wait_for_tx_confirmation(execution_client, tx_hash)
    logger.info('Transaction %s confirmed', tx_hash)
