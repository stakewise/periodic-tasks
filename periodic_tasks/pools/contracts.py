from eth_typing import ChecksumAddress
from hexbytes import HexBytes
from web3 import AsyncWeb3
from web3.types import Wei

from periodic_tasks.common.contracts import ContractWrapper
from periodic_tasks.common.execution import transaction_gas_wrapper
from periodic_tasks.common.settings import network_config

from .clients import execution_client


class MerkleDistributorContract(ContractWrapper):
    abi_path = 'abi/MerkleDistributor.json'

    async def distribute_one_time(
        self, vault: ChecksumAddress, token: ChecksumAddress, amount: Wei
    ) -> HexBytes:
        tx_function = self.contract.functions.distributeOneTime(
            token,
            amount,
            '',
            vault,
        )

        return await transaction_gas_wrapper(client=self.contract.w3, tx_function=tx_function)


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
        tx_function = self.contract.functions.approve(
            address,
            value,
        )
        return await transaction_gas_wrapper(client=self.contract.w3, tx_function=tx_function)


class SUSDsContract(ContractWrapper):
    abi_path = 'abi/Erc4626Token.json'

    async def deposit(self, assets: Wei, address: ChecksumAddress) -> HexBytes:
        tx_function = self.contract.functions.deposit(assets, address)
        return await transaction_gas_wrapper(client=self.contract.w3, tx_function=tx_function)


class WrappedEthContract(ContractWrapper):
    abi_path = 'abi/WrappedEth.json'

    async def deposit(self, value: Wei) -> HexBytes:
        tx_function = self.contract.functions.deposit()
        return await transaction_gas_wrapper(
            client=self.contract.w3, tx_function=tx_function, tx_params={'value': value}
        )


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


merkle_distributor_contract = MerkleDistributorContract(
    address=network_config.MERKLE_DISTRIBUTOR_CONTRACT_ADDRESS,
    client=execution_client,
)
