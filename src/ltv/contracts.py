import json
import logging
from pathlib import Path

from eth_typing import ChecksumAddress
from hexbytes import HexBytes
from web3.contract.contract import ContractEvents, ContractFunctions

from .clients import execution_client, hot_wallet_account
from .settings import network_config
from .typings import HarvestParams

logger = logging.getLogger(__name__)


class ContractWrapper:
    def __init__(self, abi_path: str, address: ChecksumAddress):
        self.address = address
        self.contract = execution_client.eth.contract(address=address, abi=self._load_abi(abi_path))

    def _load_abi(self, abi_path: str) -> dict:
        current_dir = Path(__file__).parent
        with open(current_dir / abi_path, encoding='utf-8') as f:
            return json.load(f)

    @property
    def functions(self) -> ContractFunctions:
        return self.contract.functions

    @property
    def events(self) -> ContractEvents:
        return self.contract.events


class VaultUserLTVTrackerContract(ContractWrapper):
    def get_vault_max_ltv(self, vault: ChecksumAddress, harvest_params: HarvestParams) -> int:
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
        self, vault: ChecksumAddress, user: ChecksumAddress, harvest_params: HarvestParams
    ) -> HexBytes:
        return self.contract.functions.updateVaultMaxLtvUser(
            vault,
            user,
            (
                harvest_params.rewards_root,
                harvest_params.reward,
                harvest_params.unlocked_mev_reward,
                harvest_params.proof,
            ),
        ).transact({'from': hot_wallet_account.address})


vault_user_ltv_tracker_contract = VaultUserLTVTrackerContract(
    abi_path='abi/IVaultUserLtvTracker.json',
    address=network_config.VAULT_USER_LTV_TRACKER_CONTRACT_ADDRESS,
)
