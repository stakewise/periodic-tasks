import logging

from eth_typing import ChecksumAddress
from web3 import Web3
from web3.types import BlockNumber, HexStr

from periodic_tasks.common.contracts import ContractWrapper
from periodic_tasks.common.settings import network_config

from .clients import execution_client

logger = logging.getLogger(__name__)


class LeverageStrategyContract(ContractWrapper):
    abi_path = 'abi/ILeverageStrategy.json'

    async def strategy_id(self) -> str:
        return await self.contract.functions.strategyId().call()


class OsTokenVaultEscrowContract(ContractWrapper):
    abi_path = 'abi/IOsTokenVaultEscrow.json'

    async def liq_threshold_percent(self) -> int:
        return await self.contract.functions.liqThresholdPercent().call()


class StrategiesRegistryContract(ContractWrapper):
    async def get_vault_ltv_percent(self, strategy_id: str) -> int:
        value = await self.contract.functions.getStrategyConfig(
            strategy_id, 'vaultForceExitLtvPercent'
        ).call()
        return Web3.to_int(value)

    async def get_borrow_ltv_percent(self, strategy_id: str) -> int:
        value = await self.contract.functions.getStrategyConfig(
            strategy_id, 'borrowForceExitLtvPercent'
        ).call()
        return Web3.to_int(value)


class KeeperContract(ContractWrapper):
    abi_path = 'abi/IKeeper.json'

    async def can_harvest(
        self, vault: ChecksumAddress, block_number: BlockNumber | None = None
    ) -> bool:
        return await self.contract.functions.canHarvest(vault).call(block_identifier=block_number)


class MulticallContract(ContractWrapper):
    abi_path = 'abi/Multicall.json'

    async def aggregate(
        self,
        data: list[tuple[ChecksumAddress, HexStr]],
        block_number: BlockNumber | None = None,
    ) -> tuple[BlockNumber, list]:
        return await self.contract.functions.aggregate(data).call(block_identifier=block_number)


leverage_strategy_contract = LeverageStrategyContract(
    address=network_config.LEVERAGE_STRATEGY_CONTRACT_ADDRESS,
    client=execution_client,
)

strategy_registry_contract = StrategiesRegistryContract(
    address=network_config.STRATEGY_REGISTRY_CONTRACT_ADDRESS,
    client=execution_client,
)

ostoken_vault_escrow_contract = OsTokenVaultEscrowContract(
    address=network_config.OSTOKEN_ESCROW_CONTRACT_ADDRESS,
    client=execution_client,
)

keeper_contract = KeeperContract(
    address=network_config.KEEPER_CONTRACT_ADDRESS,
    client=execution_client,
)

multicall_contract = MulticallContract(
    address=network_config.MULTICALL_CONTRACT_ADDRESS,
    client=execution_client,
)
