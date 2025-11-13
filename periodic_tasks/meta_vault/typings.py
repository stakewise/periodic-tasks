from dataclasses import dataclass

from eth_typing import ChecksumAddress, HexStr

from periodic_tasks.exit.typings import ExitRequest


@dataclass
class SubVaultExitRequest:
    exit_queue_index: int | None
    vault: ChecksumAddress
    timestamp: int
    position_ticket: int

    @property
    def has_exit_queue_index(self) -> bool:
        """Missing exit queue index may equal to None or -1"""
        return self.exit_queue_index is not None and self.exit_queue_index >= 0

    @staticmethod
    def from_exit_request(exit_request: ExitRequest) -> 'SubVaultExitRequest':
        return SubVaultExitRequest(
            exit_queue_index=exit_request.exit_queue_index,
            vault=exit_request.vault,
            timestamp=exit_request.timestamp,
            position_ticket=exit_request.position_ticket,
        )


@dataclass
class ContractCall:
    address: ChecksumAddress
    data: HexStr
    description: str
