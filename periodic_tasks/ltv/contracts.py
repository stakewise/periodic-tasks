import logging

from eth_typing import ChecksumAddress
from hexbytes import HexBytes
from web3 import Web3

from periodic_tasks.common.contracts import ContractWrapper
from periodic_tasks.common.settings import network_config
from periodic_tasks.common.typings import HarvestParams

from .clients import execution_client

logger = logging.getLogger(__name__)


class VaultUserLTVTrackerContract(ContractWrapper):
    async def get_max_ltv_user(self, vault: ChecksumAddress) -> ChecksumAddress:
        user = await self.contract.functions.vaultToUser(vault).call()
        return Web3.to_checksum_address(user)

    async def get_vault_max_ltv(
        self, vault: ChecksumAddress, harvest_params: HarvestParams | None
    ) -> int:
        # Create zero harvest params in case the vault has no rewards yet
        if harvest_params is None:
            harvest_params = self._get_zero_harvest_params()

        return await self.contract.functions.getVaultMaxLtv(
            vault,
            (
                harvest_params.rewards_root,
                harvest_params.reward,
                harvest_params.unlocked_mev_reward,
                harvest_params.proof,
            ),
        ).call()

    async def update_vault_max_ltv_user(
        self, vault: ChecksumAddress, user: ChecksumAddress, harvest_params: HarvestParams | None
    ) -> HexBytes:
        # Create zero harvest params in case the vault has no rewards yet
        if harvest_params is None:
            harvest_params = self._get_zero_harvest_params()

        return await self.contract.functions.updateVaultMaxLtvUser(
            vault,
            user,
            (
                harvest_params.rewards_root,
                harvest_params.reward,
                harvest_params.unlocked_mev_reward,
                harvest_params.proof,
            ),
        ).transact()


vault_user_ltv_tracker_contract = VaultUserLTVTrackerContract(
    abi_path='abi/IVaultUserLtvTracker.json',
    address=network_config.VAULT_USER_LTV_TRACKER_CONTRACT_ADDRESS,
    client=execution_client,
)
