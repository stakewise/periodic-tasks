import logging

from .clients import execution_client
from .contracts import leverage_strategy_contract, ostoken_vault_escrow_contract
from .graph import graph_get_leverage_positions, graph_osToken_exit_requests

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
