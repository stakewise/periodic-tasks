import logging
from typing import cast

from eth_typing import ChecksumAddress, HexStr
from web3 import Web3
from web3.types import BlockNumber

from src.common.settings import EXECUTION_TRANSACTION_TIMEOUT
from src.common.typings import HarvestParams

from .clients import execution_client
from .contracts import (
    VaultContract,
    get_vault_contract,
    keeper_contract,
    leverage_strategy_contract,
    multicall_contract,
    ostoken_vault_escrow_contract,
)
from .typings import ExitRequest, LeveragePosition, OsTokenExitRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def can_force_enter_exit_queue(
    vault: ChecksumAddress,
    user: ChecksumAddress,
    harvest_params: HarvestParams | None,
    block_number: BlockNumber,
) -> bool:
    vault_contract = get_vault_contract(vault)
    calls = []
    update_state_call = None
    if harvest_params and keeper_contract.can_harvest(vault, block_number):
        update_state_call = (
            vault,
            _encode_update_state_call(vault_contract, harvest_params),
        )
        calls.append(update_state_call)

    can_force_enter_exit_queue_call = leverage_strategy_contract.encode_abi(
        fn_name='canForceEnterExitQueue', args=[vault, user]
    )
    calls.append((leverage_strategy_contract.address, can_force_enter_exit_queue_call))
    # fetch data
    _, response = multicall_contract.aggregate(calls, block_number)
    if update_state_call:
        response.pop(0)
    return bool(Web3.to_int(response.pop(0)))


def vault_claim_exited_assets(
    position: LeveragePosition,
    harvest_params: HarvestParams | None,
    block_number: BlockNumber,
) -> HexStr | None:
    vault = position.vault
    vault_contract = get_vault_contract(vault)
    calls = []
    if harvest_params and keeper_contract.can_harvest(vault, block_number):
        update_state_call = (
            vault,
            _encode_update_state_call(vault_contract, harvest_params),
        )
        calls.append(update_state_call)

    exit_request = position.exit_request
    exit_request = cast(ExitRequest, exit_request)
    claim_call = vault_contract.encode_abi(
        fn_name='claimExitedAssets',
        args=[exit_request.position_ticket, exit_request.timestamp, exit_request.exit_queue_index],
    )
    calls.append((vault_contract.address, claim_call))
    try:
        tx = multicall_contract.functions.aggregate(calls).transact()
    except Exception as e:
        logger.error(
            'Failed to claim exited assets; vault=%s, user=%s %s: ', vault, position.user, e
        )
        logger.exception(e)
        return None

    tx_hash = Web3.to_hex(tx)
    logger.info('Waiting for transaction %s confirmation', tx_hash)
    tx_receipt = execution_client.eth.wait_for_transaction_receipt(
        tx, timeout=EXECUTION_TRANSACTION_TIMEOUT
    )
    if not tx_receipt['status']:
        logger.error('Exited assets claim transaction failed')
        return None

    return tx_hash


def os_token_claim_exited_assets(exit_request: OsTokenExitRequest) -> HexStr | None:
    try:
        tx = ostoken_vault_escrow_contract.claim_exited_assets(
            vault=exit_request.vault,
            exit_position_ticket=exit_request.position_ticket,
            os_token_shares=exit_request.os_token_shares,
        )
    except Exception as e:
        logger.error(
            'Failed to claim ostoken exited assets; vault=%s, position_ticket=%s %s: ',
            exit_request.vault,
            exit_request.position_ticket,
            e,
        )
        logger.exception(e)
        return None

    tx_hash = Web3.to_hex(tx)
    logger.info('Waiting for transaction %s confirmation', tx_hash)
    tx_receipt = execution_client.eth.wait_for_transaction_receipt(
        tx, timeout=EXECUTION_TRANSACTION_TIMEOUT
    )
    if not tx_receipt['status']:
        logger.error('Exited assets claim transaction failed')
        return None

    return tx_hash


def force_enter_exit_queue(vault: ChecksumAddress, user: ChecksumAddress) -> HexStr | None:
    try:
        tx = leverage_strategy_contract.force_enter_exit_queue(
            vault=vault,
            user=user,
        )
    except Exception as e:
        logger.error('Failed to force enter exit queue; vault=%s, user=%s %s: ', vault, user, e)
        logger.exception(e)
        return None

    tx_hash = Web3.to_hex(tx)
    logger.info('Waiting for transaction %s confirmation', tx_hash)
    tx_receipt = execution_client.eth.wait_for_transaction_receipt(
        tx, timeout=EXECUTION_TRANSACTION_TIMEOUT
    )
    if not tx_receipt['status']:
        logger.error('Force enter exit queue transaction failed')
        return None

    return tx_hash


def _encode_update_state_call(
    vault_contract: VaultContract, harvest_params: HarvestParams
) -> HexStr:
    return vault_contract.encode_abi(
        fn_name='updateState',
        args=[
            (
                harvest_params.rewards_root,
                harvest_params.reward,
                harvest_params.unlocked_mev_reward,
                harvest_params.proof,
            )
        ],
    )
