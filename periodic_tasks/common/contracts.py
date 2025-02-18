import json
import logging
import sys
from pathlib import Path

from eth_typing import ChecksumAddress, HexStr
from hexbytes import HexBytes
from web3 import Web3
from web3.contract.contract import ContractEvents, ContractFunctions
from web3.types import Wei

from .typings import HarvestParams

logger = logging.getLogger(__name__)


class ContractWrapper:
    abi_path: str

    def __init__(self, address: ChecksumAddress, client: Web3):
        self.address = address
        self.contract = client.eth.contract(address=address, abi=self._load_abi())

    def _load_abi(self) -> dict:
        # get subclass file path
        file = sys.modules[self.__class__.__module__].__file__
        if not file:
            raise IndexError("Can't get abi file path")
        current_dir = Path(file).parent
        with (current_dir / self.abi_path).open(encoding='utf-8') as f:
            return json.load(f)

    @property
    def functions(self) -> ContractFunctions:
        return self.contract.functions

    @property
    def events(self) -> ContractEvents:
        return self.contract.events

    def encode_abi(self, fn_name: str, args: list | None = None) -> HexStr:
        return self.contract.encodeABI(fn_name=fn_name, args=args)

    @staticmethod
    def _get_zero_harvest_params() -> HarvestParams:
        return HarvestParams(
            rewards_root=HexBytes(b'\x00' * 32), reward=Wei(0), unlocked_mev_reward=Wei(0), proof=[]
        )
