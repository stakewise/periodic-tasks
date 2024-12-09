from dataclasses import dataclass

from web3.types import ChecksumAddress, Wei


@dataclass
class ExitRequest:
    position_ticket: int
    timestamp: int
    exit_queue_index: int
    is_claimable: bool
    exited_assets: Wei
    total_assets: Wei

    @property
    def can_be_claimed(self) -> bool:
        return self.is_claimable and self.exited_assets == self.total_assets


@dataclass
class LeveragePosition:
    user: ChecksumAddress
    vault: ChecksumAddress
    proxy: ChecksumAddress
    exit_request: ExitRequest | None = None


@dataclass
class OsTokenExitRequest:
    vault: ChecksumAddress
    owner: ChecksumAddress
    position_ticket: int
    os_token_shares: Wei
    ltv: int
