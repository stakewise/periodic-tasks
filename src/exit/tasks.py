import logging

from eth_typing import ChecksumAddress
from web3.types import BlockNumber

from src.common.typings import HarvestParams
from src.ltv.graph import graph_get_harvest_params

from .clients import execution_client
from .contracts import (
    leverage_strategy_contract,
    ostoken_vault_escrow_contract,
    strategy_registry_contract,
)
from .execution import (
    can_force_enter_exit_queue,
    force_enter_exit_queue,
    os_token_claim_exited_assets,
    vault_claim_exited_assets,
)
from .graph import (
    graph_get_allocators,
    graph_get_leverage_positions,
    graph_ostoken_exit_requests,
)
from .typings import LeveragePosition

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WAD = 10**18


def force_exits() -> None:
    """
    Monitor leverage positions and trigger exits/claims for those
    that approach the liquidation threshold.
    """
    block = execution_client.eth.get_block('finalized')
    logger.debug('Current block: %d', block['number'])
    block_number = block['number']
    handle_leverage_positions(block_number)
    handel_exit_position(block_number)


def handle_leverage_positions(block_number: BlockNumber) -> None:
    """Process graph leverage positions."""
    strategy_id = leverage_strategy_contract.strategy_id()
    borrow_ltv = strategy_registry_contract.get_borrow_ltv_percent(strategy_id) / WAD
    vault_ltv = strategy_registry_contract.get_vault_ltv_percent(strategy_id) / WAD

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

        handle_leverage_position(
            position=position,
            harvest_params=harvest_params,
            block_number=block_number,
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

        handle_leverage_position(
            position=position,
            harvest_params=harvest_params,
            block_number=block_number,
        )


def handel_exit_position(block_number: BlockNumber) -> None:
    """Process osTokenExitRequests from graph and claim exited assets."""
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
        tx_hash = os_token_claim_exited_assets(exit_request)
        if tx_hash:
            logger.info(
                'Successfully claimed exited assets: vault=%s, user=%s...',
                exit_request.vault,
                exit_request.owner,
            )


def handle_leverage_position(
    position: LeveragePosition, harvest_params: HarvestParams | None, block_number: BlockNumber
) -> None:
    """
    Submit force exit for leverage postion.
    Also check for position active exit request and claim assets is we can.
    """
    if not can_force_enter_exit_queue(
        vault=position.vault,
        user=position.user,
        harvest_params=harvest_params,
        block_number=block_number,
    ):
        return
    # claim active exit request
    if position.exit_request and position.exit_request.can_be_claimed:
        logger.info(
            'Claiming exited assets for leverage positions: vault=%s, user=%s...',
            position.vault,
            position.user,
        )
        tx_hash = vault_claim_exited_assets(
            position=position,
            harvest_params=harvest_params,
            block_number=block_number,
        )
        if tx_hash:
            logger.info(
                'Successfully claimed exited assets for leverage positions: vault=%s, user=%s...',
                position.vault,
                position.user,
            )
        else:
            return
    logger.info(
        'Force exiting leverage positions: vault=%s, user=%s...',
        position.vault,
        position.user,
    )
    tx_hash = force_enter_exit_queue(
        vault=position.vault,
        user=position.user,
    )
    if tx_hash:
        logger.info(
            'Successfully triggered exit for leverage positions: vault=%s, user=%s...',
            position.vault,
            position.user,
        )
