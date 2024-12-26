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
    claim_exited_assets,
    force_enter_exit_queue,
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


async def force_exits() -> None:
    """
    Monitor leverage positions and trigger exits/claims for those
    that approach the liquidation threshold.
    """
    block = execution_client.eth.get_block('finalized')
    logger.debug('Current block: %d', block['number'])
    block_number = block['number']
    await handle_leverage_positions(block_number)
    await handle_ostoken_exit_requests(block_number)


async def handle_leverage_positions(block_number: BlockNumber) -> None:
    """Process graph leverage positions."""
    strategy_id = leverage_strategy_contract.strategy_id()
    borrow_ltv = strategy_registry_contract.get_borrow_ltv_percent(strategy_id) / WAD
    vault_ltv = strategy_registry_contract.get_vault_ltv_percent(strategy_id) / WAD
    all_leverage_positions = await graph_get_leverage_positions(block_number=block_number)
    # Get aave positions by borrow ltv
    aave_positions = [pos for pos in all_leverage_positions if pos.borrow_ltv > borrow_ltv]
    # Get vault positions by vault ltv
    proxy_to_position = {position.proxy: position for position in all_leverage_positions}
    allocators = await graph_get_allocators(
        ltv=vault_ltv, addresses=list(proxy_to_position.keys()), block_number=block_number
    )
    vault_positions = []
    for allocator in allocators:
        vault_positions.append(proxy_to_position[allocator])

    # join positions
    leverage_positions = []
    leverage_positions.extend(aave_positions)
    borrow_ltv_positions_ids = set(pos.id for pos in aave_positions)
    for position in vault_positions:
        if position.id not in borrow_ltv_positions_ids:
            leverage_positions.append(position)

    if not leverage_positions:
        logger.info('No risky leverage positions found...')
        return

    logger.info('Checking %d leverage positions...', len(leverage_positions))

    vault_to_harvest_params: dict[ChecksumAddress, HarvestParams | None] = {}
    # check by position borrow ltv
    for position in leverage_positions:
        harvest_params = vault_to_harvest_params.get(position.vault)
        if not harvest_params:
            harvest_params = await graph_get_harvest_params(position.vault)
            vault_to_harvest_params[position.vault] = harvest_params

        handle_leverage_position(
            position=position,
            harvest_params=harvest_params,
            block_number=block_number,
        )


async def handle_ostoken_exit_requests(block_number: BlockNumber) -> None:
    """Process osTokenExitRequests from graph and claim exited assets."""
    # force claim for exit positions
    max_ltv_percent = ostoken_vault_escrow_contract.liq_threshold_percent()
    max_ltv_percent = max_ltv_percent / WAD
    exit_requests = await graph_ostoken_exit_requests(max_ltv_percent, block_number=block_number)
    exit_requests = [
        exit_request for exit_request in exit_requests if exit_request.exit_request.can_be_claimed
    ]

    logger.info('Force assets claim for %d exit requests...', len(exit_requests))
    vault_to_harvest_params: dict[ChecksumAddress, HarvestParams | None] = {}

    for os_token_exit_request in exit_requests:
        vault = os_token_exit_request.vault
        harvest_params = vault_to_harvest_params.get(vault)
        if not harvest_params:
            harvest_params = await graph_get_harvest_params(vault)
            vault_to_harvest_params[vault] = harvest_params

        logger.info(
            'Claiming exited assets: vault=%s, user=%s...',
            vault,
            os_token_exit_request.owner,
        )
        tx_hash = claim_exited_assets(
            vault=vault,
            user=os_token_exit_request.owner,
            exit_request=os_token_exit_request.exit_request,
            harvest_params=harvest_params,
            block_number=block_number,
        )
        if tx_hash:
            logger.info(
                'Successfully claimed exited assets: vault=%s, user=%s...',
                vault,
                os_token_exit_request.owner,
            )


def handle_leverage_position(
    position: LeveragePosition, harvest_params: HarvestParams | None, block_number: BlockNumber
) -> None:
    """
    Submit force exit for leverage position.
    Also check for position active exit request and claim assets if possible.
    """
    if not can_force_enter_exit_queue(
        vault=position.vault,
        user=position.user,
        harvest_params=harvest_params,
        block_number=block_number,
    ):
        logger.info(
            'Skip leverage positions because it cannot be forcefully closed: vault=%s, user=%s...',
            position.vault,
            position.user,
        )
        return

    # claim active exit request
    if position.exit_request and position.exit_request.can_be_claimed:
        logger.info(
            'Claiming exited assets for leverage positions: vault=%s, user=%s...',
            position.vault,
            position.user,
        )
        tx_hash = claim_exited_assets(
            vault=position.vault,
            user=position.user,
            exit_request=position.exit_request,
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

    # recheck because position state has changed after claiming assets
    if not can_force_enter_exit_queue(
        vault=position.vault,
        user=position.user,
        harvest_params=harvest_params,
        block_number=block_number,
    ):
        logger.info(
            'Skip leverage positions because it cannot be forcefully closed: vault=%s, user=%s...',
            position.vault,
            position.user,
        )
        return

    tx_hash = force_enter_exit_queue(
        vault=position.vault,
        user=position.user,
        harvest_params=harvest_params,
        block_number=block_number,
    )
    if tx_hash:
        logger.info(
            'Successfully triggered exit for leverage positions: vault=%s, user=%s...',
            position.vault,
            position.user,
        )
