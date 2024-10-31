import json
import logging

from eth_typing import ChecksumAddress
from web3 import Web3
from web3.contract.contract import ContractEvents, ContractFunctions

logger = logging.getLogger(__name__)


class ContractWrapper:
    def __init__(self, abi_path: str, address: ChecksumAddress, client: Web3):
        self.address = address
        self.contract = client.eth.contract(address=address, abi=self._load_abi(abi_path))

    def _load_abi(self, abi_path: str) -> dict:
        with open(abi_path, encoding='utf-8') as f:
            return json.load(f)

    @property
    def functions(self) -> ContractFunctions:
        return self.contract.functions

    @property
    def events(self) -> ContractEvents:
        return self.contract.events
