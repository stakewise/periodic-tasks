import logging
from decimal import Decimal

from eth_typing import ChecksumAddress
from gql import gql
from web3 import Web3
from web3.types import Wei

from .clients import execution_client, graph_client
from .contracts import vault_user_ltv_tracker_contract
from .settings import VAULT
from .typings import HarvestParams

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# WAD is used in Solidity to work with decimals.
# Integer is interpreted as decimal multiplied by WAD
WAD = 10**18


def update_vault_max_ltv_user() -> None:
    """
    Finds user having maximum LTV in given vault and submits this user in the LTV Tracker contract.
    """
    # Get max LTV for vault
    user = graph_get_vault_max_ltv_allocator(VAULT)
    if user is None:
        logger.warning('No allocators in vault')
        return
    logger.info('max LTV user for vault %s is %s', VAULT, user)

    block = execution_client.eth.get_block('finalized')
    logger.debug('Current block: %d', block['number'])

    harvest_params = graph_get_harvest_params(VAULT)
    if not harvest_params:
        logger.warning('No harvest params for vault %s', VAULT)
        return
    logger.debug('Harvest params: %s', harvest_params)

    # Get current LTV
    ltv = vault_user_ltv_tracker_contract.get_vault_max_ltv(VAULT, harvest_params)
    logger.info('Current LTV: %s', Decimal(ltv) / WAD)

    # Update LTV
    tx = vault_user_ltv_tracker_contract.update_vault_max_ltv_user(VAULT, user, harvest_params)
    logger.info('Update transaction sent, tx hash: %s', tx.hex())

    # Wait for tx receipt
    logger.info('Waiting for tx receipt')
    receipt = execution_client.eth.wait_for_transaction_receipt(tx)

    # Check receipt status
    if not receipt['status']:
        raise RuntimeError(f'Update tx failed, tx hash: {tx.hex()}')
    logger.info('Tx confirmed')

    # Get LTV after update
    ltv = vault_user_ltv_tracker_contract.get_vault_max_ltv(VAULT, harvest_params)
    logger.info('LTV after update: %s', Decimal(ltv) / WAD)

    logger.info('Completed')


def get_vault_max_ltv() -> None:
    """
    Prints max LTV for vault
    """
    block = execution_client.eth.get_block('finalized')
    logger.debug('Current block: %d', block['number'])

    harvest_params = graph_get_harvest_params(VAULT)
    if not harvest_params:
        logger.warning('No harvest params for vault %s', VAULT)
        return
    logger.debug('Harvest params: %s', harvest_params)

    # Get current LTV
    ltv = vault_user_ltv_tracker_contract.get_vault_max_ltv(VAULT, harvest_params)
    logger.info('Current LTV: %s', Decimal(ltv) / WAD)


def graph_get_vault_max_ltv_allocator(vault_address: str) -> ChecksumAddress | None:
    query = gql(
        """
        query AllocatorsQuery($vault: String) {
          allocators(
            first: 1
            orderBy: ltv
            orderDirection: desc
            where: { vault: $vault }
          ) {
            address
          }
        }
        """
    )
    params = {
        'vault': vault_address.lower(),
    }

    response = graph_client.execute(query, params)
    allocators = response['allocators']  # pylint: disable=unsubscriptable-object

    if not allocators:
        return None

    return Web3.to_checksum_address(allocators[0]['address'])


def graph_get_harvest_params(vault_address: ChecksumAddress) -> HarvestParams | None:
    query = gql(
        """
        query VaultQuery($vault: String) {
          vault(
            id: $vault
          ) {
            id
            proof
            proofReward
            proofUnlockedMevReward
            rewardsRoot
          }
        }
        """
    )
    params = {
        'vault': vault_address.lower(),
    }

    response = graph_client.execute(query, params)
    vault_data = response['vault']  # pylint: disable=unsubscriptable-object

    if (
        vault_data['proof'] is None
        or vault_data['proofReward'] is None
        or vault_data['proofUnlockedMevReward'] is None
        or vault_data['rewardsRoot'] is None
    ):
        return None

    return HarvestParams(
        rewards_root=Web3.to_bytes(hexstr=vault_data['rewardsRoot']),
        reward=Wei(int(vault_data['proofReward'])),
        unlocked_mev_reward=Wei(int(vault_data['proofUnlockedMevReward'])),
        proof=[Web3.to_bytes(hexstr=p) for p in vault_data['proof']],
    )
