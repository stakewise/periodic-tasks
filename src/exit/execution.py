import logging

from eth_typing import ChecksumAddress, HexStr
from web3 import Web3
from web3.types import BlockNumber

from src.common.settings import EXECUTION_TRANSACTION_TIMEOUT
from src.common.typings import HarvestParams

from .clients import execution_client
from .contracts import keeper_contract, leverage_strategy_contract, multicall_contract
from .typings import ExitRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def can_force_enter_exit_queue(
    vault: ChecksumAddress,
    user: ChecksumAddress,
    harvest_params: HarvestParams | None,
    block_number: BlockNumber,
) -> bool:
    calls = []
    update_state_call = None
    if harvest_params and keeper_contract.can_harvest(vault, block_number):
        update_state_call = (
            leverage_strategy_contract.address,
            _encode_update_state_call(vault, harvest_params),
        )
        calls.append(update_state_call)

    can_force_enter_exit_queue_call = leverage_strategy_contract.encode_abi(
        fn_name='canForceEnterExitQueue', args=[vault, user]
    )
    calls.append((leverage_strategy_contract.address, can_force_enter_exit_queue_call))
    _, response = multicall_contract.aggregate(calls, block_number)
    if update_state_call:
        response.pop(0)
    return bool(Web3.to_int(response.pop(0)))


def claim_exited_assets(
    vault: ChecksumAddress,
    user: ChecksumAddress,
    exit_request: ExitRequest,
    harvest_params: HarvestParams | None,
    block_number: BlockNumber,
) -> HexStr | None:
    calls = []
    if harvest_params and keeper_contract.can_harvest(vault, block_number):
        update_state_call = (
            leverage_strategy_contract.address,
            _encode_update_state_call(vault, harvest_params),
        )
        calls.append(update_state_call)

    claim_call = leverage_strategy_contract.encode_abi(
        fn_name='claimExitedAssets',
        args=[
            vault,
            user,
            (exit_request.position_ticket, exit_request.timestamp, exit_request.exit_queue_index),
        ],
    )
    calls.append((leverage_strategy_contract.address, claim_call))
    try:
        tx = multicall_contract.functions.aggregate(calls).transact()
    except Exception as e:
        logger.info(
            'Failed to claim exited assets for leverage positions: vault=%s, user=%s %s...',
            vault,
            user,
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
        logger.info(
            'Failed to claim exited assets for leverage positions: vault=%s, user=%s...',
            vault,
            user,
        )
        return None

    return tx_hash


def force_enter_exit_queue(
    vault: ChecksumAddress,
    user: ChecksumAddress,
    harvest_params: HarvestParams | None,
    block_number: BlockNumber,
) -> HexStr | None:
    calls = []
    if harvest_params and keeper_contract.can_harvest(vault, block_number):
        update_state_call = (
            leverage_strategy_contract.address,
            _encode_update_state_call(vault, harvest_params),
        )
        calls.append(update_state_call)

    force_enter_call = leverage_strategy_contract.encode_abi(
        fn_name='forceEnterExitQueue',
        args=[vault, user],
    )
    calls.append((leverage_strategy_contract.address, force_enter_call))
    try:
        tx = multicall_contract.functions.aggregate(calls).transact()
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
    vault_address: ChecksumAddress, harvest_params: HarvestParams
) -> HexStr:
    return leverage_strategy_contract.encode_abi(
        fn_name='updateVaultState',
        args=[
            vault_address,
            (
                harvest_params.rewards_root,
                harvest_params.reward,
                harvest_params.unlocked_mev_reward,
                harvest_params.proof,
            ),
        ],
    )