from dataclasses import dataclass

from web3.types import ChecksumAddress, Wei


@dataclass
class LeveragePosition:
    user: ChecksumAddress
    vault: ChecksumAddress
    proxy: ChecksumAddress


@dataclass
class OsTokenExitRequest:
    vault: ChecksumAddress
    owner: ChecksumAddress
    position_ticket: int
    os_token_shares: Wei
    ltv: int
