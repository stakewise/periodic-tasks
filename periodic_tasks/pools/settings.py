from dataclasses import dataclass

from decouple import config
from sw_utils.networks import GNOSIS, MAINNET
from web3 import Web3
from web3.types import ChecksumAddress

from periodic_tasks.common.settings import NETWORK

ETH_TICKER = 'ETH'
GNO_TICKER = 'GNO'
BTC_TICKER = 'BTC'
SOL_TICKER = 'SOL'
SUSDS_TICKER = 'SUSDS'
SWISE_TICKER = 'SWISE'
SDAI_TICKER = 'SDAI'
BCSPX_TICKER = 'BCSPX'

NETWORK_TICKERS: dict[str, list[str]] = {
    MAINNET: [BTC_TICKER, SOL_TICKER, SUSDS_TICKER, SWISE_TICKER],
    GNOSIS: [ETH_TICKER, BTC_TICKER, SDAI_TICKER, BCSPX_TICKER],
}


TO_BTC_WALLET: str = config('BTC_WALLET', default='')
TO_SOL_WALLET: str = config('SOL_WALLET', default='')  # eth
TO_SUSDS_WALLET: str = config('SUSDS_WALLET', default='')  # eth
TO_SWISE_WALLET: str = config('SWISE_WALLET', default='')  # eth
TO_ETH_WALLET: str = config('ETH_WALLET', default='')  # gno
TO_SDAI_WALLET: str = config('SDAI_WALLET', default='')  # gno
TO_BCSPX_WALLET: str = config('BCSPX_WALLET', default='')  # gno

BTC_VAULT: str = config('BTC_VAULT', default='')
SOL_VAULT: str = config('SOL_VAULT', default='')
SUSDS_VAULT: str = config('SUSDS_VAULT', default='')
SWISE_VAULT: str = config('SWISE_VAULT', default='')
ETH_VAULT: str = config('ETH_VAULT', default='')
SDAI_VAULT: str = config('SDAI_VAULT', default='')
BCSPX_VAULT: str = config('BCSPX_VAULT', default='')


TICKER_TO_SETTINGS: dict[str, tuple[str, str]] = {
    BTC_TICKER: (TO_BTC_WALLET, BTC_VAULT),
    SOL_TICKER: (TO_SOL_WALLET, SOL_VAULT),
    SUSDS_TICKER: (TO_SUSDS_WALLET, SUSDS_VAULT),
    SWISE_TICKER: (TO_SWISE_WALLET, SWISE_VAULT),
    ETH_TICKER: (TO_ETH_WALLET, ETH_VAULT),
    SDAI_VAULT: (TO_SDAI_WALLET, SDAI_VAULT),
    BCSPX_TICKER: (TO_BCSPX_WALLET, BCSPX_VAULT),
}


@dataclass
class Data:
    ticker: str
    wallet_address: ChecksumAddress
    vault_address: ChecksumAddress


DDDATA: list[Data] = []
for ticker in NETWORK_TICKERS[NETWORK]:
    if all(TICKER_TO_SETTINGS.get(ticker, [])):
        DDDATA.append(
            Data(
                ticker=ticker,
                wallet_address=Web3.to_checksum_address(TICKER_TO_SETTINGS[ticker][0]),
                vault_address=Web3.to_checksum_address(TICKER_TO_SETTINGS[ticker][1]),
            )
        )


TOKEN_ADDRESSES = {
    MAINNET: {
        ETH_TICKER: Web3.to_checksum_address('0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE'),
        BTC_TICKER: Web3.to_checksum_address('0x2260fac5e5542a773aa44fbcfedf7c193bc2c599'),
        SOL_TICKER: Web3.to_checksum_address('0xD31a59c85aE9D8edEFeC411D448f90841571b89c'),
        SUSDS_TICKER: Web3.to_checksum_address('0xa3931d71877c0e7a3148cb7eb4463524fec27fbd'),
        SWISE_TICKER: Web3.to_checksum_address('0x48c3399719b582dd63eb5aadf12a40b4c3f52fa2'),
    },
    GNOSIS: {
        'DAI': Web3.to_checksum_address('0x00000000000000000'),  # todo
        GNO_TICKER: Web3.to_checksum_address('0x9C58BAcC331c9aa871AFD802DB6379a98e80CEdb'),
        ETH_TICKER: Web3.to_checksum_address('0x6A023CCd1ff6F2045C3309768eAd9E68F978f6e1'),
        BTC_TICKER: Web3.to_checksum_address('0x8e5bbbb09ed1ebde8674cda39a0c169401db4252'),
        SDAI_TICKER: Web3.to_checksum_address('0xaf204776c7245bF4147c2612BF6e5972Ee483701'),
        BCSPX_TICKER: Web3.to_checksum_address('0x1e2C4fb7eDE391d116E6B41cD0608260e8801D59'),
    },
}

NETWORK_BASE_TICKER_ADDRESSES = {
    MAINNET: TOKEN_ADDRESSES[MAINNET][ETH_TICKER],
    GNOSIS: TOKEN_ADDRESSES[GNOSIS][GNO_TICKER],
}
COWSWAP_REQUEST_TIMEOUT: int = config('COWSWAP_REQUEST_TIMEOUT', default='60', cast=int)
COWSWAP_ORDER_PROCESSING_TIMEOUT: int = config(
    'COWSWAP_ORDER_PROCESSING_TIMEOUT', default='60', cast=int
)
