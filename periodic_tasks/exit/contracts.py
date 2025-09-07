import logging

from eth_typing import ChecksumAddress
from web3 import Web3

from periodic_tasks.common.contracts import ContractWrapper
from periodic_tasks.common.settings import network_config

from .clients import execution_client

logger = logging.getLogger(__name__)


class LeverageStrategyContract(ContractWrapper):
    ...


class StrategyProxyContract(ContractWrapper):
    ...


class OsTokenVaultEscrowContract(ContractWrapper):
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


strategy_registry_contract = StrategiesRegistryContract(
    abi_path='abi/IStrategyRegistry.json',
    address=network_config.STRATEGY_REGISTRY_CONTRACT_ADDRESS,
    client=execution_client,
)

ostoken_vault_escrow_contract = OsTokenVaultEscrowContract(
    abi_path='abi/IOsTokenVaultEscrow.json',
    address=network_config.OSTOKEN_VAULT_ESCROW_CONTRACT_ADDRESS,
    client=execution_client,
)


async def get_strategy_proxy_contract(proxy: ChecksumAddress) -> StrategyProxyContract:
    return StrategyProxyContract(
        abi_path='abi/IStrategyProxy.json',
        address=proxy,
        client=execution_client,
    )


async def get_leverage_strategy_contract(proxy: ChecksumAddress) -> LeverageStrategyContract:
    proxy_contract = await get_strategy_proxy_contract(proxy)
    leverage_strategy_address = await proxy_contract.contract.functions.owner().call()
    return LeverageStrategyContract(
        abi_path='abi/ILeverageStrategy.json',
        address=leverage_strategy_address,
        client=execution_client,
    )
