from dataclasses import dataclass

from eth_typing import ChecksumAddress, HexStr

from periodic_tasks.exit.typings import ExitRequest


@dataclass
class SubVaultExitRequest:
    exit_queue_index: int
    vault: ChecksumAddress
    timestamp: int

    @staticmethod
    def from_exit_request(exit_request: ExitRequest) -> 'SubVaultExitRequest':
        if exit_request.exit_queue_index is None:
            raise ValueError('Exit request does not have an exit queue index')

        return SubVaultExitRequest(
            exit_queue_index=exit_request.exit_queue_index,
            vault=exit_request.vault,
            timestamp=exit_request.timestamp,
        )


@dataclass
class ContractCall:
    address: ChecksumAddress
    data: HexStr
    description: str
