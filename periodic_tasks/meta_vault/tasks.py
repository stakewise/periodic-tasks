import logging

from periodic_tasks.common.execution import wait_for_tx_confirmation
from periodic_tasks.ltv import settings

from eth_typing import ChecksumAddress
from web3 import Web3
from web3.types import BlockNumber, HexStr
from sw_utils import convert_to_mgno

from periodic_tasks.common.settings import network_config, NETWORK, GNO_NETWORKS
from periodic_tasks.meta_vault.contracts import MetaVaultContract

from .clients import execution_client

logger = logging.getLogger(__name__)


async def process_all_meta_vaults() -> None:
    for vault in settings.VAULTS:
        logger.info('Processing meta vault: %s', vault)
        await process_deposit_to_subvaults(vault)


async def process_deposit_to_subvaults(vault: str) -> None:
    meta_vault_contract = MetaVaultContract(
        abi_path='abi/IEthMetaVault.json',
        address=vault,
        client=execution_client,
    )
    withdrawable_assets = await meta_vault_contract.withdrawable_assets()

    logger.info(
        'Meta vault %s has withdrawable assets: %s',
        vault,
        Web3.from_wei(withdrawable_assets, 'ether'),
    )

    if NETWORK in GNO_NETWORKS:
        withdrawable_assets = convert_to_mgno(withdrawable_assets)

    if withdrawable_assets < settings.METAVAULT_MIN_DEPOSIT_AMOUNT:
        return

    logger.info('Depositing to subvaults for meta vault %s', vault)
    tx_hash = await meta_vault_contract.deposit_to_subvaults()

    logger.info('Waiting for transaction %s confirmation', tx_hash)
    await wait_for_tx_confirmation(tx_hash)
    logger.info('Transaction %s confirmed', tx_hash)
