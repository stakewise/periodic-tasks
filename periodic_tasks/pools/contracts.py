import logging

from eth_typing import ChecksumAddress
from hexbytes import HexBytes
from web3 import Web3
from web3.types import Wei

from periodic_tasks.common.contracts import ContractWrapper
from periodic_tasks.common.settings import network_config

from .clients import execution_client

logger = logging.getLogger(__name__)


class TokenDistributorContract(ContractWrapper):
    def distribute_one_time(
        self, vault: ChecksumAddress, token: ChecksumAddress, amount: Wei
    ) -> HexBytes:
        return self.contract.functions.distributeOneTime(
            token,
            amount,
            '',
            vault,
        ).transact()


class Erc20Contract(ContractWrapper):
    abi_path = 'abi/Erc20Token.json'

    async def symbol(self) -> str:
        return await self.contract.functions.symbol().call()

    def get_balance(
        self,
        address: ChecksumAddress,
    ) -> Wei:
        return self.contract.functions.balanceOf(address).call()

    def get_allowance(
        self,
        owner: ChecksumAddress,
        spender: ChecksumAddress,
    ) -> Wei:
        return self.contract.functions.allowance(owner, spender).call()

    def approve(self, address: ChecksumAddress, value: Wei) -> HexBytes:
        return self.contract.functions.approve(
            address,
            value,
        ).transact()


def get_erc20_contract(address: ChecksumAddress, client: Web3 | None = None) -> Erc20Contract:
    if not client:
        client = execution_client
    return Erc20Contract(
        abi_path='abi/Erc20Token.json',
        address=address,
        client=client,
    )


token_distributor_contract = TokenDistributorContract(
    abi_path='abi/TokenDistributor.json',
    address=network_config.TOKEN_DISTRIBUTOR_CONTRACT_ADDRESS,
    client=execution_client,
)
