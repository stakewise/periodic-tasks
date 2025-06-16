import json
import logging
import sys
from pathlib import Path

from hexbytes import HexBytes
from web3 import AsyncWeb3
from web3.contract.async_contract import AsyncContractEvents, AsyncContractFunctions
from web3.types import BlockNumber, ChecksumAddress, HexStr, Wei

from periodic_tasks.common.settings import network_config
from periodic_tasks.exit.clients import execution_client

from .typings import HarvestParams

logger = logging.getLogger(__name__)


class ContractWrapper:
    def __init__(self, abi_path: str, address: ChecksumAddress, client: AsyncWeb3):
        self.address = address
        self.contract = client.eth.contract(address=address, abi=self._load_abi(abi_path))

    def _load_abi(self, abi_path: str) -> dict:
        # get subclass file path
        file = sys.modules[self.__class__.__module__].__file__
        if not file:
            raise IndexError("Can't get abi file path")
        current_dir = Path(file).parent
        with (current_dir / abi_path).open(encoding='utf-8') as f:
            return json.load(f)

    @property
    def functions(self) -> AsyncContractFunctions:
        return self.contract.functions

    @property
    def events(self) -> AsyncContractEvents:
        return self.contract.events

    def encode_abi(self, fn_name: str, args: list | None = None) -> HexStr:
        return self.contract.encodeABI(fn_name=fn_name, args=args)

    @staticmethod
    def _get_zero_harvest_params() -> HarvestParams:
        return HarvestParams(
            rewards_root=HexBytes(b'\x00' * 32), reward=Wei(0), unlocked_mev_reward=Wei(0), proof=[]
        )


class VaultStateEncoderMixin:
    def __init__(self, contract: ContractWrapper):
        self.contract = contract

    def update_vault_state(self, harvest_params: HarvestParams) -> HexStr:
        return self.contract.encode_abi(
            fn_name='updateVaultState',
            args=[
                (
                    harvest_params.rewards_root,
                    harvest_params.reward,
                    harvest_params.unlocked_mev_reward,
                    harvest_params.proof,
                ),
            ],
        )


class VaultEncoder(VaultStateEncoderMixin):
    pass


class VaultContract(ContractWrapper):
    def encoder(self) -> VaultEncoder:
        return VaultEncoder(self)


class MulticallContract(ContractWrapper):
    async def aggregate(
        self,
        data: list[tuple[ChecksumAddress, HexStr]],
        block_number: BlockNumber | None = None,
    ) -> tuple[BlockNumber, list]:
        return await self.contract.functions.aggregate(data).call(block_identifier=block_number)

    async def tx_aggregate(
        self,
        data: list[tuple[ChecksumAddress, HexStr]],
    ) -> HexStr:
        tx_hash = await self.contract.functions.aggregate(data).transact()
        return HexStr(tx_hash.hex())


multicall_contract = MulticallContract(
    abi_path='abi/Multicall.json',
    address=network_config.MULTICALL_CONTRACT_ADDRESS,
    client=execution_client,
)
