import logging

from eth_typing import ChecksumAddress
from gql import gql
from hexbytes import HexBytes
from sw_utils.graph.client import GraphClient
from web3 import Web3
from web3.types import Wei

from periodic_tasks.common.typings import HarvestParams

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def get_harvest_params(
    graph_client: GraphClient, vault_address: ChecksumAddress
) -> HarvestParams | None:
    query = gql(
        """
        query VaultQuery($vault: String) {
          vault(
            id: $vault
          ) {
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

    response = await graph_client.run_query(query, params)
    vault_data = response['vault']  # pylint: disable=unsubscriptable-object

    if not all(vault_data):
        return None

    return HarvestParams(
        rewards_root=HexBytes(Web3.to_bytes(hexstr=vault_data['rewardsRoot'])),
        reward=Wei(int(vault_data['proofReward'])),
        unlocked_mev_reward=Wei(int(vault_data['proofUnlockedMevReward'])),
        proof=[HexBytes(Web3.to_bytes(hexstr=p)) for p in vault_data['proof']],
    )


async def get_multiple_harvest_params(
    graph_client: GraphClient, vaults: list[ChecksumAddress]
) -> dict[ChecksumAddress, HarvestParams]:
    query = gql(
        """
      query VaultQuery($vaults: [String]) {
        vaults(
          where: {
            id_in: $vaults
          }
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
        'vaults': [v.lower() for v in vaults],
    }

    response = await graph_client.run_query(query, params)
    vault_data = response['vaults']  # pylint: disable=unsubscriptable-object

    harvest_params_map: dict[ChecksumAddress, HarvestParams] = {}

    for vault_item in vault_data:
        harvest_params = HarvestParams(
            rewards_root=HexBytes(Web3.to_bytes(hexstr=vault_item['rewardsRoot'])),
            reward=Wei(int(vault_item['proofReward'])),
            unlocked_mev_reward=Wei(int(vault_item['proofUnlockedMevReward'])),
            proof=[HexBytes(Web3.to_bytes(hexstr=p)) for p in vault_item['proof']],
        )
        harvest_params_map[Web3.to_checksum_address(vault_item['id'])] = harvest_params

    return harvest_params_map
