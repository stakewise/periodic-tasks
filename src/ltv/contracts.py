import logging

from eth_typing import ChecksumAddress
from hexbytes import HexBytes
from web3 import Web3
from web3.types import Wei

from src.common.contracts import ContractWrapper
from src.common.settings import network_config

from .clients import execution_client
from .typings import HarvestParams

logger = logging.getLogger(__name__)

ABI_DIR = 'src/ltv/abi'


class VaultUserLTVTrackerContract(ContractWrapper):
    def get_max_ltv_user(self, vault: ChecksumAddress) -> ChecksumAddress:
        user = self.contract.functions.vaultToUser(vault).call()
        return Web3.to_checksum_address(user)

    def get_vault_max_ltv(
        self, vault: ChecksumAddress, harvest_params: HarvestParams | None
    ) -> int:
        # Create zero harvest params in case the vault has no rewards yet
        if harvest_params is None:
            harvest_params = self._get_zero_harvest_params()

        return self.contract.functions.getVaultMaxLtv(
            vault,
            (
                harvest_params.rewards_root,
                harvest_params.reward,
                harvest_params.unlocked_mev_reward,
                harvest_params.proof,
            ),
        ).call()

    def update_vault_max_ltv_user(
        self, vault: ChecksumAddress, user: ChecksumAddress, harvest_params: HarvestParams | None
    ) -> HexBytes:
        # Create zero harvest params in case the vault has no rewards yet
        if harvest_params is None:
            harvest_params = self._get_zero_harvest_params()

        return self.contract.functions.updateVaultMaxLtvUser(
            vault,
            user,
            (
                harvest_params.rewards_root,
                harvest_params.reward,
                harvest_params.unlocked_mev_reward,
                harvest_params.proof,
            ),
        ).transact()

    @staticmethod
    def _get_zero_harvest_params() -> HarvestParams:
        return HarvestParams(
            rewards_root=HexBytes(b'\x00' * 32), reward=Wei(0), unlocked_mev_reward=Wei(0), proof=[]
        )


vault_user_ltv_tracker_contract = VaultUserLTVTrackerContract(
    abi_path=f'{ABI_DIR}/IVaultUserLtvTracker.json',
    address=network_config.VAULT_USER_LTV_TRACKER_CONTRACT_ADDRESS,
    client=execution_client,
)
