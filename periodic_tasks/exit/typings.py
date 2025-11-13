from dataclasses import dataclass

from web3 import Web3
from web3.types import ChecksumAddress, Wei


@dataclass
class ExitRequest:
    id: str
    vault: ChecksumAddress
    position_ticket: int
    timestamp: int
    exit_queue_index: int | None
    is_claimed: bool
    is_claimable: bool
    exited_assets: Wei
    total_assets: Wei

    @property
    def is_fully_claimable(self) -> bool:
        return self.is_claimable and self.exited_assets == self.total_assets

    @property
    def is_waiting_for_claim_delay(self) -> bool:
        """
        Returns True if the assets have exited (fully or partially),
        but the claim delay has not passed yet.
        Relevant for testnets with short exit queues (e.g., Chiado)
        """
        return self.has_exit_queue_index and not self.is_claimable and not self.is_claimed

    @property
    def has_exit_queue_index(self) -> bool:
        """Missing exit queue index may equal to None or -1"""
        return self.exit_queue_index is not None and self.exit_queue_index >= 0

    @staticmethod
    def from_graph(data: dict) -> 'ExitRequest':
        exit_queue_index = (
            int(data['exitQueueIndex']) if data.get('exitQueueIndex') is not None else None
        )
        return ExitRequest(
            id=data['id'],
            vault=Web3.to_checksum_address(data['vault']['id']),
            position_ticket=int(data['positionTicket']),
            timestamp=int(data['timestamp']),
            exit_queue_index=exit_queue_index,
            is_claimed=data['isClaimed'],
            is_claimable=data['isClaimable'],
            exited_assets=Wei(int(data['exitedAssets'])),
            total_assets=Wei(int(data['totalAssets'])),
        )


@dataclass
class LeveragePosition:
    user: ChecksumAddress
    vault: ChecksumAddress
    proxy: ChecksumAddress
    borrow_ltv: float
    exit_request: ExitRequest | None = None

    @property
    def id(self) -> str:
        return f'{self.vault}-{self.user}'


@dataclass
class OsTokenExitRequest:
    id: str
    vault: ChecksumAddress
    owner: ChecksumAddress
    ltv: int
    exit_request: ExitRequest
