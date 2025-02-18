from dataclasses import dataclass

from eth_account.signers.local import LocalAccount
from sw_utils.networks import MAINNET
from web3.types import ChecksumAddress

from periodic_tasks.common.settings import NETWORK

from .settings import (
    NETWORK_BASE_TICKER_ADDRESSES,
    SUSDS_TICKER,
    TOKEN_ADDRESSES,
    USDS_TICKER,
    WETH_TICKER,
)


@dataclass
class PoolSettings:
    ticker: str
    wallet: LocalAccount
    vault_address: ChecksumAddress

    # @property
    # def wallet_address(self) -> ChecksumAddress:
    #     return self.wallet.address

    @property
    def swap_from_token(self) -> ChecksumAddress:
        if NETWORK == MAINNET:
            return TOKEN_ADDRESSES[MAINNET][WETH_TICKER]
        return NETWORK_BASE_TICKER_ADDRESSES[NETWORK]

    @property
    def swap_to_token(self) -> ChecksumAddress:
        if self.ticker == SUSDS_TICKER:
            return TOKEN_ADDRESSES[NETWORK][USDS_TICKER]
        return TOKEN_ADDRESSES[NETWORK][self.ticker]

    @property
    def distribute_token(self) -> ChecksumAddress:
        return TOKEN_ADDRESSES[NETWORK][self.ticker]
