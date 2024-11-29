import logging

from eth_typing import ChecksumAddress
from hexbytes import HexBytes
from web3.types import Wei

from src.common.clients import hot_wallet_account
from src.common.contracts import ContractWrapper
from src.common.settings import network_config

from .clients import execution_client

logger = logging.getLogger(__name__)

ABI_DIR = 'src/exit/abi'


class LeverageStrategyContract(ContractWrapper):
    def can_force_enter_exit_queue(self, vault: ChecksumAddress, user: ChecksumAddress) -> bool:
        return self.contract.functions.canForceEnterExitQueue(vault, user).call()

    def force_enter_exit_queue(
        self,
        vault: ChecksumAddress,
        user: ChecksumAddress,
    ) -> HexBytes:
        return self.contract.functions.forceEnterExitQueue(
            vault,
            user,
        ).transact({'from': hot_wallet_account.address})


class OsTokenVaultEscrowContract(ContractWrapper):
    def liq_threshold_percent(self) -> int:
        return self.contract.functions.liqThresholdPercent().call()

    def claim_exited_assets(
        self,
        vault: ChecksumAddress,
        exit_position_ticket: int,
        os_token_shares: Wei,
    ) -> HexBytes:
        return self.contract.functions.claimExitedAssets(
            vault,
            exit_position_ticket,
            os_token_shares,
        ).transact({'from': hot_wallet_account.address})


leverage_strategy_contract = LeverageStrategyContract(
    abi_path=f'{ABI_DIR}/ILeverageStrategy.json',
    address=network_config.LEVERAGE_STRATEGY_CONTRACT_ADDRESS,
    client=execution_client,
)

ostoken_vault_escrow_contract = OsTokenVaultEscrowContract(
    abi_path=f'{ABI_DIR}/IOsTokenVaultEscrow.json',
    address=network_config.VAULT_ESCROW_CONTRACT_ADDRESS,
    client=execution_client,
)
