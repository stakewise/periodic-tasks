import logging

from eth_typing import ChecksumAddress, HexStr

from periodic_tasks.common.contracts import ContractWrapper
from periodic_tasks.common.typings import HarvestParams

logger = logging.getLogger(__name__)


SOLIDITY_UINT256_MAX = 2**256 - 1


class RewardSplitterContract(ContractWrapper):
    def get_update_vault_state_call(self, harvest_params: HarvestParams) -> HexStr:
        return self.encode_abi(
            fn_name='updateVaultState',
            args=[
                (
                    harvest_params.rewards_root,
                    harvest_params.reward,
                    harvest_params.unlocked_mev_reward,
                    harvest_params.proof,
                ),
            ],
        )

    def get_enter_exit_queue_on_behalf_call(
        self, rewards: int | None, address: ChecksumAddress
    ) -> HexStr:
        rewards = rewards or SOLIDITY_UINT256_MAX
        return self.encode_abi(
            fn_name='enterExitQueueOnBehalf',
            args=[rewards, address],
        )
