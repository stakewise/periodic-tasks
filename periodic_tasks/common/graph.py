import logging

from eth_typing import ChecksumAddress
from gql import gql
from hexbytes import HexBytes
from sw_utils.graph.client import GraphClient
from web3 import Web3
from web3.types import Wei

from periodic_tasks.common.typings import Vault

logger = logging.getLogger(__name__)


async def graph_get_vaults(
    graph_client: GraphClient,
    vaults: list[ChecksumAddress] | None = None,
    is_meta_vault: bool | None = None,
) -> dict[ChecksumAddress, Vault]:
    """
    Returns mapping from vault address to Vault object
    """
    where_conditions: list[str] = []
    params: dict = {}

    if vaults:
        where_conditions.append('id_in: $vaults')
        params['vaults'] = [v.lower() for v in vaults]

    if is_meta_vault is not None:
        where_conditions.append('isMetaVault: $isMetaVault')
        params['isMetaVault'] = is_meta_vault

    where_conditions_str = '\n'.join(where_conditions)
    where_clause = f'where: {{ {where_conditions_str} }}' if where_conditions else ''

    filters = ['first: $first', 'skip: $skip']

    if where_clause:
        filters.append(where_clause)

    query = f"""
        query VaultQuery($first: Int, $skip: Int, $vaults: [String], $isMetaVault: Boolean) {{
            vaults(
                {', '.join(filters)}
            ) {{
                id
                isMetaVault
                subVaults {{
                    subVault
                }}
                canHarvest
                proof
                proofReward
                proofUnlockedMevReward
                rewardsRoot
            }}
        }}
        """

    response = await graph_client.fetch_pages(gql(query), params)

    graph_vaults_map: dict[ChecksumAddress, Vault] = {}

    for vault_item in response:
        vault = _convert_vault_item_to_vault(vault_item)
        graph_vaults_map[vault.address] = vault

    return graph_vaults_map


def _convert_vault_item_to_vault(vault_item: dict) -> Vault:
    vault_address = Web3.to_checksum_address(vault_item['id'])
    is_meta_vault = vault_item['isMetaVault']

    sub_vaults = [
        Web3.to_checksum_address(sub_vault['subVault']) for sub_vault in vault_item['subVaults']
    ]

    can_harvest = vault_item['canHarvest']

    # rewardsRoot
    vault_address = Web3.to_checksum_address(vault_item['id'])
    is_meta_vault = vault_item['isMetaVault']

    sub_vaults = [
        Web3.to_checksum_address(sub_vault['subVault']) for sub_vault in vault_item['subVaults']
    ]

    can_harvest = vault_item['canHarvest']

    # rewardsRoot
    if vault_item['rewardsRoot'] is None:
        rewards_root = HexBytes(b'\x00' * 32)
    else:
        rewards_root = HexBytes(Web3.to_bytes(hexstr=vault_item['rewardsRoot']))

    # proofReward
    if vault_item['proofReward'] is None:
        proof_reward = Wei(0)
    else:
        proof_reward = Wei(int(vault_item['proofReward']))

    # proofUnlockedMevReward
    if vault_item['proofUnlockedMevReward'] is None:
        proof_unlocked_mev_reward = Wei(0)
    else:
        proof_unlocked_mev_reward = Wei(int(vault_item['proofUnlockedMevReward']))

    # proof
    if vault_item['proof'] is None:
        proof = []
    else:
        proof = [HexBytes(Web3.to_bytes(hexstr=p)) for p in vault_item['proof']]

    return Vault(
        address=vault_address,
        is_meta_vault=is_meta_vault,
        sub_vaults=sub_vaults,
        can_harvest=can_harvest,
        rewards_root=rewards_root,
        proof_reward=proof_reward,
        proof_unlocked_mev_reward=proof_unlocked_mev_reward,
        proof=proof,
    )
