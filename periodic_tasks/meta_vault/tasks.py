import logging

from eth_typing import ChecksumAddress
from sw_utils import GNO_NETWORKS, convert_to_mgno
from web3 import Web3
from web3.types import BlockNumber, HexStr

from periodic_tasks.common.clients import execution_client
from periodic_tasks.common.contracts import VaultContract, multicall_contract
from periodic_tasks.common.execution import wait_for_tx_confirmation
from periodic_tasks.common.graph import graph_get_vaults
from periodic_tasks.common.networks import ZERO_CHECKSUM_ADDRESS
from periodic_tasks.common.settings import NETWORK
from periodic_tasks.common.typings import Vault
from periodic_tasks.exit.graph import graph_get_exit_requests_by_vaults
from periodic_tasks.meta_vault.contracts import MetaVaultContract
from periodic_tasks.meta_vault.graph import graph_get_meta_vaults
from periodic_tasks.meta_vault.typings import SubVaultExitRequest

from . import settings
from .clients import graph_client

logger = logging.getLogger(__name__)


async def process_all_meta_vaults(block_number: BlockNumber) -> None:
    meta_vaults_map = await graph_get_meta_vaults(settings.META_VAULTS)

    for meta_vault_address, meta_vault in meta_vaults_map.items():
        logger.info('Processing meta vault: %s', meta_vault_address)
        await meta_vault_update_state(
            meta_vault=meta_vault,
            block_number=block_number,
        )
        await process_deposit_to_sub_vaults(meta_vault_address=meta_vault_address)


async def meta_vault_update_state(
    meta_vault: Vault,
    block_number: BlockNumber,
) -> None:
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

    # Collect exit requests for the sub vaults
    vault_to_exit_requests = await graph_get_exit_requests_by_vaults(
        vaults=meta_vault.sub_vaults,
        block_number=block_number,
    )
    sub_vault_exit_requests: list[SubVaultExitRequest] = []

    for exit_requests in vault_to_exit_requests.values():
        for exit_request in exit_requests:
            if not exit_request.is_claimable:
                continue
            sub_vault_exit_requests.append(SubVaultExitRequest.from_exit_request(exit_request))

    # Meta vault contract
    meta_vault_contract = MetaVaultContract(
        abi_path='abi/IEthMetaVault.json',
        address=meta_vault.address,
        client=execution_client,
    )
    meta_vault_encoder = meta_vault_contract.encoder()

    # Claim sub vaults exited assets
    if sub_vault_exit_requests:
        calls.append(
            (
                meta_vault.address,
                meta_vault_encoder.claim_sub_vaults_exited_assets(sub_vault_exit_requests),
            )
        )

    # Update meta vault state
    calls.append((meta_vault.address, meta_vault_encoder.update_state(meta_vault.harvest_params)))

    # Submit the transaction
    tx_hash = await multicall_contract.tx_aggregate(calls)

    logger.info('Waiting for transaction %s confirmation', tx_hash)
    await wait_for_tx_confirmation(execution_client, tx_hash)
    logger.info('Transaction %s confirmed', tx_hash)


async def process_deposit_to_sub_vaults(meta_vault_address: ChecksumAddress) -> None:
    meta_vault_contract = MetaVaultContract(
        abi_path='abi/IEthMetaVault.json',
        address=meta_vault_address,
        client=execution_client,
    )
    withdrawable_assets = await meta_vault_contract.withdrawable_assets()

    logger.info(
        'Meta vault %s has withdrawable assets: %s',
        meta_vault_address,
        Web3.from_wei(withdrawable_assets, 'ether'),
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
