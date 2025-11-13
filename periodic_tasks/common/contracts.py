import json
import logging
import sys
from pathlib import Path
from typing import cast

from hexbytes import HexBytes
from web3 import AsyncWeb3
from web3.contract.async_contract import (
    AsyncContractEvent,
    AsyncContractEvents,
    AsyncContractFunctions,
)
from web3.types import BlockNumber, ChecksumAddress, EventData, HexStr, TxParams, Wei

from .clients import execution_client
from .settings import EVENTS_BLOCKS_RANGE_INTERVAL, GAS_LIMIT, network_config
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

    async def _get_last_event(
        self,
        event: type[AsyncContractEvent],
        from_block: BlockNumber,
        to_block: BlockNumber,
        argument_filters: dict | None = None,
    ) -> EventData | None:
        blocks_range = EVENTS_BLOCKS_RANGE_INTERVAL
        while to_block >= from_block:
            events = await event.get_logs(
                fromBlock=BlockNumber(max(to_block - blocks_range, from_block)),
                toBlock=to_block,
                argument_filters=argument_filters,
            )
            if events:
                return events[-1]
            to_block = BlockNumber(to_block - blocks_range - 1)
        return None


class VaultEncoder:
    def __init__(self, contract: ContractWrapper):
        self.contract = contract

    def update_state(self, harvest_params: HarvestParams) -> HexStr:
        return self.contract.encode_abi(
            fn_name='updateState',
            args=[
                (
                    harvest_params.rewards_root,
                    harvest_params.reward,
                    harvest_params.unlocked_mev_reward,
                    harvest_params.proof,
                ),
            ],
        )


class VaultContract(ContractWrapper):
    def encoder(self) -> VaultEncoder:
        return VaultEncoder(self)

    async def get_exit_queue_index(self, position_ticket: int) -> int:
        return await self.contract.functions.getExitQueueIndex(position_ticket).call()


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
        tx_params: TxParams = {}
        if GAS_LIMIT > 0:
            tx_params['gas'] = GAS_LIMIT
        tx_hash = await self.contract.functions.aggregate(data).transact(tx_params)
        return HexStr(tx_hash.hex())


class KeeperContract(ContractWrapper):
    async def can_harvest(
        self, vault: ChecksumAddress, block_number: BlockNumber | None = None
    ) -> bool:
        return await self.contract.functions.canHarvest(vault).call(block_identifier=block_number)

    async def get_last_rewards_updated_event(
        self, from_block: BlockNumber, to_block: BlockNumber
    ) -> EventData | None:
        return await self._get_last_event(
            cast(type[AsyncContractEvent], self.contract.events.RewardsUpdated),
            from_block=from_block,
            to_block=to_block,
        )


def get_vault_contract(address: ChecksumAddress) -> VaultContract:
    return VaultContract(
        abi_path='abi/IEthVault.json',
        address=address,
        client=execution_client,
    )


multicall_contract = MulticallContract(
    abi_path='abi/Multicall.json',
    address=network_config.MULTICALL_CONTRACT_ADDRESS,
    client=execution_client,
)


keeper_contract = KeeperContract(
    abi_path='abi/IKeeper.json',
    address=network_config.KEEPER_CONTRACT_ADDRESS,
    client=execution_client,
)
