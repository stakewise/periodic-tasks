import logging

from eth_typing import ChecksumAddress
from hexbytes import HexBytes
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


token_distributor_contract = TokenDistributorContract(
    abi_path='abi/IVaultUserLtvTracker.json',
    address=network_config.TOKEN_DISTRIBUTOR_CONTRACT_ADDRESS,
    client=execution_client,
)
