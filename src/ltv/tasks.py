import logging
from datetime import timedelta
from decimal import Decimal

from eth_typing import BlockNumber, ChecksumAddress
from gql import gql
from sw_utils import convert_to_gno
from web3 import Web3

from src.ltv.networks import GNO_NETWORKS

from .clients import execution_client, graph_client, ipfs_fetch_client
from .contracts import keeper_contract, vault_user_ltv_tracker_contract
from .settings import NETWORK, VAULT, network_config
from .typings import HarvestParams, RewardSnapshot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# WAD is used in Solidity to work with decimals.
# Integer is interpreted as decimal multiplied by WAD
WAD = 10**18


async def update_vault_max_ltv_user() -> None:
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

    harvest_params = await get_harvest_params(VAULT, block['number'])
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


async def get_vault_max_ltv() -> None:
    """
    Prints max LTV for vault
    """
    block = execution_client.eth.get_block('finalized')
    logger.debug('Current block: %d', block['number'])

    harvest_params = await get_harvest_params(VAULT, block['number'])
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


async def get_harvest_params(
    vault: ChecksumAddress, block_number: BlockNumber
) -> HarvestParams | None:
    to_block = block_number
    events_interval = int(timedelta(days=7).total_seconds())
    from_block = to_block - events_interval // network_config.SECONDS_PER_BLOCK

    event = keeper_contract.get_rewards_updated_event(
        from_block=BlockNumber(from_block), to_block=to_block
    )
    if event is None:
        logger.warning('RewardsUpdated event not found')
        return None

    ipfs_hash = event['args']['rewardsIpfsHash']
    rewards_root = event['args']['rewardsRoot']
    rewards_data = await ipfs_fetch_client.fetch_json(ipfs_hash)
    vault_to_harvest_params = get_vault_to_harvest_params(
        reward_snapshot=RewardSnapshot.from_dict(rewards_data),
        rewards_root=rewards_root,
    )
    return vault_to_harvest_params.get(vault)


def get_vault_to_harvest_params(
    reward_snapshot: RewardSnapshot, rewards_root: bytes
) -> dict[ChecksumAddress, HarvestParams]:
    results = {}
    for vault_data in reward_snapshot.vaults:
        vault, reward, unlocked_mev_reward = vault_data.merkle_leaf
        if NETWORK in GNO_NETWORKS:
            reward = convert_to_gno(reward)
        results[vault] = HarvestParams(
            rewards_root=rewards_root,
            reward=reward,
            unlocked_mev_reward=unlocked_mev_reward,
            proof=[Web3.to_bytes(hexstr=x) for x in vault_data.proof],
        )

    return results
