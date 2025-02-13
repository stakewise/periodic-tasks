from dataclasses import dataclass

from eth_account.signers.local import LocalAccount
from web3.types import ChecksumAddress


@dataclass
class PoolSettings:
    ticker: str
    wallet: LocalAccount
    vault_address: ChecksumAddress

    @property
    def wallet_address(self) -> ChecksumAddress:
        return self.wallet.address
