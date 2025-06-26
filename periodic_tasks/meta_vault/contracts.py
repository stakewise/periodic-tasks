import logging
from typing import cast

from eth_typing import BlockNumber, HexStr
from web3 import Web3
from web3.contract.async_contract import AsyncContractEvent
from web3.types import EventData, Wei

from periodic_tasks.common.contracts import ContractWrapper
from periodic_tasks.common.typings import HarvestParams
from periodic_tasks.meta_vault.typings import SubVaultExitRequest

logger = logging.getLogger(__name__)


class MetaVaultContract(ContractWrapper):
    async def withdrawable_assets(self) -> Wei:
        return await self.contract.functions.withdrawableAssets().call()

    async def deposit_to_sub_vaults(self) -> HexStr:
        tx_hash = await self.contract.functions.depositToSubVaults().transact()
        return Web3.to_hex(tx_hash)

    def encoder(self) -> 'MetaVaultEncoder':
        return MetaVaultEncoder(self)

    async def get_last_rewards_nonce_updated_event(
        self, from_block: BlockNumber, to_block: BlockNumber
    ) -> EventData | None:
        """
        Returns the latest RewardsNonceUpdated event data from the contract.
        """
        event = await self._get_last_event(
            event=cast(type[AsyncContractEvent], self.contract.events.RewardsNonceUpdated),
            from_block=from_block,
            to_block=to_block,
        )
        return event


class MetaVaultEncoder:
    def __init__(self, contract: MetaVaultContract):
        self.contract = contract

    def claim_sub_vaults_exited_assets(
        self, sub_vault_exit_requests: list[SubVaultExitRequest]
    ) -> HexStr:
        exit_requests_arg: list[tuple] = []

        for request in sub_vault_exit_requests:
            exit_requests_arg.append(
                (
                    request.exit_queue_index,
                    request.vault,
                    request.timestamp,
                )
            )
        return self.contract.encode_abi(
            fn_name='claimSubVaultsExitedAssets', args=[exit_requests_arg]
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
