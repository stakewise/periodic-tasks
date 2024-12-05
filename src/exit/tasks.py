import logging

from eth_typing import ChecksumAddress, HexStr
from web3 import Web3
from web3.types import BlockNumber

from src.common.settings import EXECUTION_TRANSACTION_TIMEOUT
from src.common.typings import HarvestParams
from src.ltv.graph import graph_get_harvest_params

from .clients import execution_client
from .contracts import (
    VaultContract,
    get_vault_contract,
    keeper_contract,
    leverage_strategy_contract,
    multicall_contract,
    ostoken_vault_escrow_contract,
    strategy_registry_contract,
)
from .graph import (
    graph_get_allocators,
    graph_get_leverage_positions,
    graph_ostoken_exit_requests,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def force_exits() -> None:
    """
    Monitor leverage positions and trigger exits/claims for those
    that approach the liquidation threshold.
    """
    block = execution_client.eth.get_block('finalized')
    logger.debug('Current block: %d', block['number'])
    block_number = block['number']
    # force exit leverage positions

    strategy_id = leverage_strategy_contract.strategy_id()
    borrow_ltv = strategy_registry_contract.get_borrow_ltv_percent(strategy_id)
    vault_ltv = strategy_registry_contract.get_vault_ltv_percent(strategy_id)

    leverage_positions = graph_get_leverage_positions(
        borrow_ltv=borrow_ltv, block_number=block_number
    )
    logger.info('Checking %d leverage positions...', len(leverage_positions))

    vault_to_harvest_params: dict[ChecksumAddress, HarvestParams | None] = {}
    # check by position borrow ltv
    for position in leverage_positions:
        harvest_params = vault_to_harvest_params.get(position.vault)
        if not harvest_params:
            harvest_params = graph_get_harvest_params(position.vault)
            vault_to_harvest_params[position.vault] = harvest_params

        if can_force_enter_exit_queue(
            vault=position.vault,
            user=position.user,
            harvest_params=harvest_params,
            block_number=block_number,
        ):
            logger.info(
                'Force exiting leverage positions: vault=%s, user=%s...',
                position.vault,
                position.user,
            )
            tx_hash = _force_enter_exit_queue(
                vault=position.vault,
                user=position.user,
            )
            if tx_hash:
                logger.info(
                    'Successfully triggered exit for leverage positions: vault=%s, user=%s...',
                    position.vault,
                    position.user,
                )

    # check by position proxy ltv
    proxy_to_position = {position.proxy: position for position in leverage_positions}
    allocators = graph_get_allocators(
        ltv=vault_ltv, addresses=list(proxy_to_position.keys()), block_number=block_number
    )
    leverage_positions_by_ltv = []
    for allocator in allocators:
        leverage_positions_by_ltv.append(proxy_to_position[allocator])

    for position in leverage_positions_by_ltv:
        harvest_params = vault_to_harvest_params.get(position.vault)
        if not harvest_params:
            harvest_params = graph_get_harvest_params(position.vault)
            vault_to_harvest_params[position.vault] = harvest_params

        if can_force_enter_exit_queue(
            vault=position.vault,
            user=position.user,
            harvest_params=harvest_params,
            block_number=block_number,
        ):
            logger.info(
                'Force exiting leverage positions: vault=%s, user=%s...',
                position.vault,
                position.user,
            )
            leverage_strategy_contract.force_enter_exit_queue(
                vault=position.vault,
                user=position.user,
            )
            logger.info(
                'Successfully exited leverage positions: vault=%s, user=%s...',
                position.vault,
                position.user,
            )

    # force claim for exit positions
    max_ltv_percent = ostoken_vault_escrow_contract.liq_threshold_percent()
    max_ltv_percent = max_ltv_percent // 10**18 * 100
    exit_requests = graph_ostoken_exit_requests(max_ltv_percent, block_number=block_number)
    logger.info('Force assets claim for %d exit requests...', len(exit_requests))

    for exit_request in exit_requests:
        logger.info(
            'Claiming exited assets: vault=%s, user=%s...',
            exit_request.vault,
            exit_request.owner,
        )
        ostoken_vault_escrow_contract.claim_exited_assets(
            vault=exit_request.vault,
            exit_position_ticket=exit_request.position_ticket,
            os_token_shares=exit_request.os_token_shares,
        )
        logger.info(
            'Successfully claimed exited assets: vault=%s, user=%s...',
            exit_request.vault,
            exit_request.owner,
        )


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


def _force_enter_exit_queue(vault: ChecksumAddress, user: ChecksumAddress) -> HexStr | None:
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
