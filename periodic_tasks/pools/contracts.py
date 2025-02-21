import logging

from eth_typing import ChecksumAddress
from hexbytes import HexBytes
from web3 import AsyncWeb3
from web3.types import Wei

from periodic_tasks.common.contracts import ContractWrapper
from periodic_tasks.common.settings import network_config

from .clients import execution_client

logger = logging.getLogger(__name__)


class TokenDistributorContract(ContractWrapper):
    abi_path = 'abi/TokenDistributor.json'

    async def distribute_one_time(
        self, vault: ChecksumAddress, token: ChecksumAddress, amount: Wei
    ) -> HexBytes:
        return await self.contract.functions.distributeOneTime(
            token,
            amount,
            '',
            vault,
        ).transact()


class Erc20Contract(ContractWrapper):
    abi_path = 'abi/Erc20Token.json'

    async def get_balance(
        self,
        address: ChecksumAddress,
    ) -> Wei:
        return await self.contract.functions.balanceOf(address).call()

    async def get_allowance(
        self,
        owner: ChecksumAddress,
        spender: ChecksumAddress,
    ) -> Wei:
        return await self.contract.functions.allowance(owner, spender).call()

    async def approve(self, address: ChecksumAddress, value: Wei) -> HexBytes:
        return await self.contract.functions.approve(
            address,
            value,
        ).transact()


class SUSDsContract(ContractWrapper):
    abi_path = 'abi/Erc4626Token.json'

    async def deposit(self, assets: Wei, address: ChecksumAddress) -> HexBytes:
        return await self.contract.functions.deposit(assets, address).transact()


class WrappedEthContract(ContractWrapper):
    abi_path = 'abi/WrappedEth.json'

    async def deposit(self, value: Wei) -> HexBytes:
        return await self.contract.functions.deposit().transact({'value': value})


def get_erc20_contract(address: ChecksumAddress, client: AsyncWeb3 | None = None) -> Erc20Contract:
    if not client:
        client = execution_client
    return Erc20Contract(
        address=address,
        client=client,
    )


def get_wrapped_eth_contract(address: ChecksumAddress, client: AsyncWeb3) -> WrappedEthContract:
    return WrappedEthContract(
        address=address,
        client=client,
    )


def get_susds_contract(address: ChecksumAddress, client: AsyncWeb3) -> SUSDsContract:
    return SUSDsContract(
        address=address,
        client=client,
    )


token_distributor_contract = TokenDistributorContract(
    address=network_config.TOKEN_DISTRIBUTOR_CONTRACT_ADDRESS,
    client=execution_client,
)
