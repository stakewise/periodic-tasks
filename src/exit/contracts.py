import logging

from eth_typing import ChecksumAddress
from hexbytes import HexBytes
from web3 import Web3
from web3.types import BlockNumber, HexStr, Wei

from src.common.contracts import ContractWrapper
from src.common.settings import network_config

from .clients import execution_client

logger = logging.getLogger(__name__)

ABI_DIR = 'src/exit/abi'


class LeverageStrategyContract(ContractWrapper):
    def strategy_id(self) -> str:
        return self.contract.functions.strategyId().call()

    def force_enter_exit_queue(
        self,
        vault: ChecksumAddress,
        user: ChecksumAddress,
    ) -> HexBytes:
        return self.contract.functions.forceEnterExitQueue(
            vault,
            user,
        ).transact()


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
        ).transact()


class StrategiesRegistryContract(ContractWrapper):
    def get_vault_ltv_percent(self, strategy_id: str) -> int:
        value = self.contract.functions.getStrategyConfig(
            strategy_id, 'vaultForceExitLtvPercent'
        ).call()
        return Web3.to_int(value)

    def get_borrow_ltv_percent(self, strategy_id: str) -> int:
        value = self.contract.functions.getStrategyConfig(
            strategy_id, 'borrowForceExitLtvPercent'
        ).call()
        return Web3.to_int(value)


class VaultContract(ContractWrapper):
    ...


class KeeperContract(ContractWrapper):
    def can_harvest(self, vault: ChecksumAddress, block_number: BlockNumber) -> bool:
        return self.contract.functions.canHarvest(vault).call(block_identifier=block_number)


class MulticallContract(ContractWrapper):
    def aggregate(
        self,
        data: list[tuple[ChecksumAddress, HexStr]],
        block_number: BlockNumber | None = None,
    ) -> tuple[BlockNumber, list]:
        return self.contract.functions.aggregate(data).call(block_identifier=block_number)


leverage_strategy_contract = LeverageStrategyContract(
    abi_path=f'{ABI_DIR}/ILeverageStrategy.json',
    address=network_config.LEVERAGE_STRATEGY_CONTRACT_ADDRESS,
    client=execution_client,
)

strategy_registry_contract = StrategiesRegistryContract(
    abi_path=f'{ABI_DIR}/IStrategyRegistry.json',
    address=network_config.STRATEGY_REGISTRY_CONTRACT_ADDRESS,
    client=execution_client,
)

ostoken_vault_escrow_contract = OsTokenVaultEscrowContract(
    abi_path=f'{ABI_DIR}/IOsTokenVaultEscrow.json',
    address=network_config.OSTOKEN_ESCROW_CONTRACT_ADDRESS,
    client=execution_client,
)

keeper_contract = KeeperContract(
    abi_path=f'{ABI_DIR}/IKeeper.json',
    address=network_config.KEEPER_CONTRACT_ADDRESS,
    client=execution_client,
)

multicall_contract = MulticallContract(
    abi_path=f'{ABI_DIR}/Multicall.json',
    address=network_config.MULTICALL_CONTRACT_ADDRESS,
    client=execution_client,
)


def get_vault_contract(address: ChecksumAddress) -> VaultContract:
    return VaultContract(
        abi_path=f'{ABI_DIR}/IEthVault.json',
        address=address,
        client=execution_client,
    )
