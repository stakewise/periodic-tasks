from eth_typing import ChecksumAddress

from periodic_tasks.common.graph import get_graph_vaults
from periodic_tasks.common.typings import Vault

from .clients import graph_client


async def graph_get_metavaults(
    meta_vault_addresses: list[ChecksumAddress],
) -> dict[ChecksumAddress, Vault]:
    vaults = await get_graph_vaults(
        graph_client=graph_client,
        vaults=meta_vault_addresses,
    )

    for vault in vaults.values():
        if not vault.is_meta_vault:
            raise ValueError(f'Vault {vault.address} is not a Meta Vault')

    return vaults
