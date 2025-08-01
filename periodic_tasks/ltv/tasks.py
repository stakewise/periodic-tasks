import logging
from decimal import Decimal

from periodic_tasks.common.graph import graph_get_vaults

from .clients import execution_client, graph_client
from .contracts import vault_user_ltv_tracker_contract
from .graph import graph_get_ostoken_vaults, graph_get_vault_max_ltv_allocator
from .typings import VaultMaxLtvUser

logger = logging.getLogger(__name__)

# WAD is used in Solidity to work with decimals.
# Integer is interpreted as decimal multiplied by WAD
WAD = 10**18


async def update_vault_max_ltv_user() -> None:
    """
    Finds user having maximum LTV in given vault and submits this user in the LTV Tracker contract.
    """
    block = await execution_client.eth.get_block('finalized')
    logger.debug('Current block: %d', block['number'])

    # Get max LTV user for vault
    max_ltv_users = await get_max_ltv_users()

    if not max_ltv_users:
        logger.info('No max LTV users found. Nothing to update.')
        return

    for user in max_ltv_users:
        if user.address == user.prev_address:
            logger.info('Max LTV user did not change since last update. Skip updating user.')
            continue

        logger.info('Updating max LTV user for vault %s', user.vault)
        await handle_max_ltv_user(user)

    logger.info('Completed')


async def get_max_ltv_users() -> list[VaultMaxLtvUser]:
    ostoken_vaults = await graph_get_ostoken_vaults()

    if not ostoken_vaults:
        logger.info('No OsToken vaults found')
        return []

    max_ltv_users = []
    graph_vaults = await graph_get_vaults(graph_client=graph_client, vaults=ostoken_vaults)

    for vault in ostoken_vaults:
        max_ltv_user_address = await graph_get_vault_max_ltv_allocator(vault)
        if max_ltv_user_address is None:
            logger.warning('No allocators in vault %s', vault)
            continue
        logger.info('max LTV user for vault %s is %s', vault, max_ltv_user_address)

        harvest_params = graph_vaults[vault].harvest_params
        logger.debug('Harvest params for vault %s: %s', vault, harvest_params)

        # Get current LTV
        ltv = await vault_user_ltv_tracker_contract.get_vault_max_ltv(vault, harvest_params)
        logger.info('Current LTV for vault %s: %s', vault, Decimal(ltv) / WAD)

        # Get prev max LTV user
        prev_max_ltv_user_address = await vault_user_ltv_tracker_contract.get_max_ltv_user(vault)

        # Build VaultMaxLtvUser object
        max_ltv_users.append(
            VaultMaxLtvUser(
                address=max_ltv_user_address,
                prev_address=prev_max_ltv_user_address,
                vault=vault,
                ltv=ltv,
                harvest_params=harvest_params,
            )
        )

    return max_ltv_users


async def handle_max_ltv_user(max_ltv_user: VaultMaxLtvUser) -> None:
    vault = max_ltv_user.vault
    # Update LTV
    tx = await vault_user_ltv_tracker_contract.update_vault_max_ltv_user(
        vault, max_ltv_user.address, max_ltv_user.harvest_params
    )
    logger.info('Update transaction sent, tx hash: %s', tx.hex())

    # Wait for tx receipt
    logger.info('Waiting for tx receipt')
    receipt = await execution_client.eth.wait_for_transaction_receipt(tx)

    # Check receipt status
    if not receipt['status']:
        raise RuntimeError(f'Update tx failed, tx hash: {tx.hex()}')
    logger.info('Tx confirmed')

    # Get LTV after update
    ltv = await vault_user_ltv_tracker_contract.get_vault_max_ltv(
        vault, max_ltv_user.harvest_params
    )
    logger.info('LTV for vault %s after update: %s', vault, Decimal(ltv) / WAD)
