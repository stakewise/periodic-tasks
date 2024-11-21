import logging
from decimal import Decimal

from .clients import execution_client
from .contracts import vault_user_ltv_tracker_contract
from .graph import (
    graph_get_harvest_params,
    graph_get_ostoken_vaults,
    graph_get_vault_max_ltv_allocator,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# WAD is used in Solidity to work with decimals.
# Integer is interpreted as decimal multiplied by WAD
WAD = 10**18


def update_vault_max_ltv_user() -> None:
    """
    Finds user having maximum LTV in given vault and submits this user in the LTV Tracker contract.
    """
    # Get max LTV user for vault

    block = execution_client.eth.get_block('finalized')
    logger.debug('Current block: %d', block['number'])
    ostoken_vaults = graph_get_ostoken_vaults()
    for vault in ostoken_vaults:
        max_ltv_user = graph_get_vault_max_ltv_allocator(vault)
        if max_ltv_user is None:
            logger.warning('No allocators in vault %s', vault)
            continue
        logger.info('max LTV user for vault %s is %s', vault, max_ltv_user)

        harvest_params = graph_get_harvest_params(vault)
        if not harvest_params:
            logger.warning('No harvest params for vault %s', vault)
            continue
        logger.debug('Harvest params: %s', harvest_params)

        # Get current LTV
        ltv = vault_user_ltv_tracker_contract.get_vault_max_ltv(vault, harvest_params)
        logger.info('Current LTV for vault %s: %s', vault, Decimal(ltv) / WAD)

        # Get prev max LTV user
        prev_max_ltv_user = vault_user_ltv_tracker_contract.get_max_ltv_user(vault)
        if max_ltv_user == prev_max_ltv_user:
            logger.info('Max LTV user did not change since last update. Skip updating user.')
            continue

        # Update LTV
        tx = vault_user_ltv_tracker_contract.update_vault_max_ltv_user(
            vault, max_ltv_user, harvest_params
        )
        logger.info('Update transaction sent, tx hash: %s', tx.hex())

        # Wait for tx receipt
        logger.info('Waiting for tx receipt')
        receipt = execution_client.eth.wait_for_transaction_receipt(tx)

        # Check receipt status
        if not receipt['status']:
            raise RuntimeError(f'Update tx failed, tx hash: {tx.hex()}')
        logger.info('Tx confirmed')

        # Get LTV after update
        ltv = vault_user_ltv_tracker_contract.get_vault_max_ltv(vault, harvest_params)
        logger.info('LTV for vault %s after update: %s', vault, Decimal(ltv) / WAD)

    logger.info('Completed')
