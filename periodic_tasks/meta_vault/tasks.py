import logging

from eth_typing import ChecksumAddress
from sw_utils import GNO_NETWORKS, convert_to_mgno
from web3 import Web3
from web3.types import BlockNumber, HexStr

from periodic_tasks.common.clients import execution_client
from periodic_tasks.common.contracts import (
    VaultContract,
    keeper_contract,
    multicall_contract,
)
from periodic_tasks.common.execution import wait_for_tx_confirmation
from periodic_tasks.common.graph import graph_get_vaults
from periodic_tasks.common.networks import ZERO_CHECKSUM_ADDRESS
from periodic_tasks.common.settings import NETWORK, network_config
from periodic_tasks.common.typings import Vault
from periodic_tasks.exit.graph import graph_get_claimable_exit_requests_by_vaults
from periodic_tasks.meta_vault.contracts import MetaVaultContract
from periodic_tasks.meta_vault.graph import graph_get_meta_vaults
from periodic_tasks.meta_vault.typings import SubVaultExitRequest

from . import settings
from .clients import graph_client

logger = logging.getLogger(__name__)


async def process_meta_vaults() -> None:
    meta_vaults_map = await graph_get_meta_vaults(settings.META_VAULTS)
    vaults_updated: set[ChecksumAddress] = set()

    for meta_vault_address, meta_vault in meta_vaults_map.items():
        logger.info('Processing meta vault: %s', meta_vault_address)
        await meta_vault_tree_update_state(
            root_meta_vault=meta_vault,
            meta_vaults_map=meta_vaults_map,
            vaults_updated=vaults_updated,
        )
        await process_deposit_to_sub_vaults(meta_vault_address=meta_vault_address)


async def meta_vault_tree_update_state(
    root_meta_vault: Vault,
    meta_vaults_map: dict[ChecksumAddress, Vault],
    vaults_updated: set[ChecksumAddress],
) -> None:
    """
    Update the state for the root meta vault and all its sub vaults.
    Sub vaults may themselves be meta vaults, so the update traverses the entire meta vault tree.
    """
    calls = await _get_meta_vault_tree_update_state_calls(
        root_meta_vault=root_meta_vault,
        meta_vaults_map=meta_vaults_map,
        vaults_updated=vaults_updated,
    )
    if not calls:
        logger.info('Meta vault %s state is up-to-date, no updates needed', root_meta_vault.address)
        return

    # Submit the transaction
    logger.info(
        'Submitting transaction to update state for meta vault tree %s',
        root_meta_vault.address,
    )
    tx_hash = await multicall_contract.tx_aggregate(calls)

    logger.info('Waiting for transaction %s confirmation', tx_hash)
    await wait_for_tx_confirmation(execution_client, tx_hash)
    logger.info('Transaction %s confirmed', tx_hash)


async def _get_meta_vault_tree_update_state_calls(
    root_meta_vault: Vault,
    meta_vaults_map: dict[ChecksumAddress, Vault],
    vaults_updated: set[ChecksumAddress],
) -> list[tuple[ChecksumAddress, HexStr]]:
    """
    Traverses meta vault tree and collects state update calls.
    """
    stack = [root_meta_vault.address]
    calls: list[tuple[ChecksumAddress, HexStr]] = []

    while stack:
        # Take the last meta vault
        meta_vault_address = stack.pop()
        meta_vault = meta_vaults_map[meta_vault_address]

        if meta_vault.address in vaults_updated:
            logger.info(
                'Meta vault %s is already updated as a part of another meta vault tree',
                meta_vault.address,
            )
            continue

        # Get calls for a single meta vault
        # not following multi vaults among sub vaults
        meta_vault_calls = await _get_meta_vault_update_state_calls(
            meta_vault=meta_vault,
        )
        # Filter out already updated vaults
        meta_vault_calls = [c for c in meta_vault_calls if c[0] not in vaults_updated]

        # Insert new calls at the start
        calls = meta_vault_calls + calls

        for sub_vault in meta_vault.sub_vaults:
            # Schedule sub vault for processing if it is meta vault
            if sub_vault in meta_vaults_map and sub_vault not in vaults_updated:
                stack.append(sub_vault)
                continue

            # Mark sub vault as updated
            if sub_vault not in meta_vaults_map:
                vaults_updated.add(sub_vault)

        # Mark the root meta vault as updated
        vaults_updated.add(meta_vault.address)

    return calls


async def _get_meta_vault_update_state_calls(
    meta_vault: Vault,
) -> list[tuple[ChecksumAddress, HexStr]]:
    """
    Get state update calls for a single meta vault and its sub vaults.
    Do not follow multi vaults among sub vaults.
    """
    # Get sub vaults
    sub_vaults = await graph_get_vaults(
        graph_client=graph_client,
        vaults=meta_vault.sub_vaults,
    )
    sub_vaults_to_harvest: list[ChecksumAddress] = []
    calls: list[tuple[ChecksumAddress, HexStr]] = []

    # Vault contract
    vault_encoder = VaultContract(
        abi_path='abi/IEthVault.json',
        address=ZERO_CHECKSUM_ADDRESS,
        client=execution_client,
    ).encoder()

    # Filter harvestable sub vaults and prepare calls for updating their state
    for sub_vault in sub_vaults.values():
        if not sub_vault.can_harvest:
            continue

        # Handle nested meta vaults separately
        if sub_vault.is_meta_vault:
            continue

        logger.info('Sub vault %s is harvestable', sub_vault.address)
        sub_vaults_to_harvest.append(sub_vault.address)
        calls.append(
            (
                sub_vault.address,
                vault_encoder.update_state(
                    sub_vault.harvest_params,
                ),
            )
        )

    if not sub_vaults_to_harvest:
        logger.info('No harvestable sub vaults for meta vault %s', meta_vault.address)

    # Collect claimable exit requests for the sub vaults
    sub_vault_exit_requests = await get_claimable_sub_vault_exit_requests(
        sub_vaults=meta_vault.sub_vaults,
    )

    # Meta vault contract
    meta_vault_contract = MetaVaultContract(
        abi_path='abi/IEthMetaVault.json',
        address=meta_vault.address,
        client=execution_client,
    )
    meta_vault_encoder = meta_vault_contract.encoder()

    # Claim sub vaults exited assets
    if sub_vault_exit_requests:
        logger.info(
            'Meta vault has %d sub vault exit requests to claim',
            len(sub_vault_exit_requests),
        )
        calls.append(
            (
                meta_vault.address,
                meta_vault_encoder.claim_sub_vaults_exited_assets(sub_vault_exit_requests),
            )
        )
    else:
        logger.info('No sub vault exit requests to claim for meta vault')

    # Update meta vault state
    is_rewards_nonce_outdated = await is_meta_vault_rewards_nonce_outdated(
        meta_vault_contract=meta_vault_contract,
    )

    if sub_vaults_to_harvest or is_rewards_nonce_outdated:
        calls.append(
            (meta_vault.address, meta_vault_encoder.update_state(meta_vault.harvest_params))
        )
    return calls


async def get_claimable_sub_vault_exit_requests(
    sub_vaults: list[ChecksumAddress],
) -> list[SubVaultExitRequest]:
    """
    Get claimable exit requests for the given sub vaults.
    """
    vault_to_exit_requests = await graph_get_claimable_exit_requests_by_vaults(
        vaults=sub_vaults,
        block_number=await execution_client.eth.get_block_number(),
    )

    claimable_exit_requests: list[SubVaultExitRequest] = []
    for exit_requests in vault_to_exit_requests.values():
        for exit_request in exit_requests:
            claimable_exit_requests.append(SubVaultExitRequest.from_exit_request(exit_request))

    return claimable_exit_requests


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

    return meta_vault_event is not None


async def process_deposit_to_sub_vaults(meta_vault_address: ChecksumAddress) -> None:
    meta_vault_contract = MetaVaultContract(
        abi_path='abi/IEthMetaVault.json',
        address=meta_vault_address,
        client=execution_client,
    )
    withdrawable_assets = await meta_vault_contract.withdrawable_assets()

    logger.info(
        'Meta vault %s has withdrawable assets: %.2f %s',
        meta_vault_address,
        Web3.from_wei(withdrawable_assets, 'ether'),
        network_config.VAULT_BALANCE_UNIT,
    )

    if NETWORK in GNO_NETWORKS:
        withdrawable_assets = convert_to_mgno(withdrawable_assets)

    if withdrawable_assets < settings.META_VAULT_MIN_DEPOSIT_AMOUNT:
        return

    logger.info('Depositing to sub vaults for meta vault %s', meta_vault_address)
    tx_hash = await meta_vault_contract.deposit_to_sub_vaults()

    logger.info('Waiting for transaction %s confirmation', tx_hash)
    await wait_for_tx_confirmation(execution_client, tx_hash)
    logger.info('Transaction %s confirmed', tx_hash)
