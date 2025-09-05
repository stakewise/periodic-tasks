import logging

from eth_typing import ChecksumAddress
from gql import gql
from sw_utils.graph.client import GraphClient

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
        vault = Vault.from_graph(vault_item)
        graph_vaults_map[vault.address] = vault

    return graph_vaults_map
