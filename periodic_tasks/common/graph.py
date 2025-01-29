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
