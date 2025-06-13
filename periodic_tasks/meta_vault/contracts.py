from eth_typing import HexStr
from web3 import Web3
from periodic_tasks.common.contracts import ContractWrapper
from web3.types import Wei


class MetaVaultContract(ContractWrapper):
    async def withdrawable_assets(self) -> Wei:
        return await self.contract.functions.withdrawableAssets().call()

    async def deposit_to_subvaults(self) -> HexStr:
        tx_hash = await self.contract.functions.depositToSubVaults().transact()
        return Web3.to_hex(tx_hash)
