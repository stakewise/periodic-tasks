from eth_typing import ChecksumAddress

from periodic_tasks.common.graph import graph_get_vaults
from periodic_tasks.common.typings import Vault

from .clients import graph_client


async def graph_get_meta_vaults(
    meta_vault_addresses: list[ChecksumAddress],
) -> dict[ChecksumAddress, Vault]:
    vaults = await graph_get_vaults(
        graph_client=graph_client,
        vaults=meta_vault_addresses,
    )

    for vault in vaults.values():
        if not vault.is_meta_vault:
            raise ValueError(f'Vault {vault.address} is not a Meta Vault')

    return vaults
