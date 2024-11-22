import logging

from eth_typing import ChecksumAddress
from gql import gql
from hexbytes import HexBytes
from web3 import Web3
from web3.types import Wei

from .clients import graph_client
from .typings import HarvestParams

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def graph_get_ostoken_vaults() -> list[ChecksumAddress]:
    query = gql(
        """
        query OsTokenVaultsIds {
          networks {
            osTokenVaultIds
          }
        }
        """
    )

    response = graph_client.execute(query)
    vaults = response['networks'][0]['osTokenVaultIds']  # pylint: disable=unsubscriptable-object
    return [Web3.to_checksum_address(vault) for vault in vaults]


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

    if not all(vault_data):
        return None

    return HarvestParams(
        rewards_root=HexBytes(Web3.to_bytes(hexstr=vault_data['rewardsRoot'])),
        reward=Wei(int(vault_data['proofReward'])),
        unlocked_mev_reward=Wei(int(vault_data['proofUnlockedMevReward'])),
        proof=[HexBytes(Web3.to_bytes(hexstr=p)) for p in vault_data['proof']],
    )
