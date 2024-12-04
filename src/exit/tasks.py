import logging

from eth_typing import ChecksumAddress, HexStr
from web3 import Web3

from src.common.settings import EXECUTION_TRANSACTION_TIMEOUT

from .clients import execution_client
from .contracts import leverage_strategy_contract, ostoken_vault_escrow_contract
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
    leverage_positions = graph_get_leverage_positions(block_number=block_number)
    logger.info('Checking %d leverage positions...', len(leverage_positions))

    # check by position borrow ltv
    for position in leverage_positions:
        if leverage_strategy_contract.can_force_enter_exit_queue(
            vault=position.vault,
            user=position.user,
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
        else:
            # position sorted by ltv and next will have lower ltv
            break

    # check by position proxy ltv
    proxy_to_position = {position.proxy: position for position in leverage_positions}
    allocators = graph_get_allocators(list(proxy_to_position.keys()), block_number=block_number)
    leverage_positions_by_ltv = []
    for allocator in allocators:
        leverage_positions_by_ltv.append(proxy_to_position[allocator])

    for position in leverage_positions_by_ltv:
        if leverage_strategy_contract.can_force_enter_exit_queue(
            vault=position.vault,
            user=position.user,
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
        else:
            # position sorted by ltv and next will have lower ltv
            break

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
