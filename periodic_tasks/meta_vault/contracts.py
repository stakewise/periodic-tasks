from eth_typing import HexStr
from web3 import Web3
from web3.types import Wei

from periodic_tasks.common.contracts import ContractWrapper
from periodic_tasks.common.typings import HarvestParams
from periodic_tasks.meta_vault.typings import SubVaultExitRequest


class MetaVaultContract(ContractWrapper):
    async def withdrawable_assets(self) -> Wei:
        return await self.contract.functions.withdrawableAssets().call()

    async def deposit_to_sub_vaults(self) -> HexStr:
        tx_hash = await self.contract.functions.depositToSubVaults().transact()
        return Web3.to_hex(tx_hash)

    def encoder(self) -> 'MetaVaultEncoder':
        return MetaVaultEncoder(self)


class MetaVaultEncoder:
    def __init__(self, contract: MetaVaultContract):
        self.contract = contract

    def claim_sub_vaults_exited_assets(
        self, sub_vault_exit_requests: list[SubVaultExitRequest]
    ) -> HexStr:
        return self.contract.encode_abi(
            fn_name='claimSubVaultsExitedAssets', args=sub_vault_exit_requests
        )

    def update_state(self, harvest_params: HarvestParams) -> HexStr:
        return self.contract.encode_abi(
            fn_name='updateState',
            args=[
                (
                    harvest_params.rewards_root,
                    harvest_params.reward,
                    harvest_params.unlocked_mev_reward,
                    harvest_params.proof,
                ),
            ],
        )
