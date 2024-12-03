import logging

from .clients import execution_client
from .contracts import leverage_strategy_contract, ostoken_vault_escrow_contract
from .graph import (
    graph_get_allocators,
    graph_get_leverage_positions,
    graph_osToken_exit_requests,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def force_exits() -> None:
    """Force handle ltv overflow. Trigger os token position exits"""
    # Get max LTV user for vault
    block = execution_client.eth.get_block('finalized')
    logger.debug('Current block: %d', block['number'])

    # force exit leverage positions
    leverage_positions = graph_get_leverage_positions()
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

    # check by position proxy ltv
    # addresses = [position.proxy for position in leverage_positions]
    proxy_to_position = {position.proxy: position for position in leverage_positions}
    allocators = graph_get_allocators(list(proxy_to_position.keys()))
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
    exit_requests = graph_osToken_exit_requests(str(max_ltv_percent / 10**18))
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

    logger.info('Completed')
