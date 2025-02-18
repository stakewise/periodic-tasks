from decouple import config
from eth_account.signers.local import LocalAccount
from sw_utils.networks import GNOSIS, MAINNET
from web3 import Web3

from periodic_tasks.common.clients import get_hot_wallet_account

ETH_TICKER = 'ETH'
WETH_TICKER = 'WETH'
DAI_TICKER = 'DAI'
GNO_TICKER = 'GNO'
BTC_TICKER = 'BTC'
SOL_TICKER = 'SOL'
USDS_TICKER = 'USDS'
SUSDS_TICKER = 'SUSDS'
SWISE_TICKER = 'SWISE'
SDAI_TICKER = 'SDAI'
BCSPX_TICKER = 'BCSPX'

NETWORK_TICKERS: dict[str, list[str]] = {
    MAINNET: [BTC_TICKER, SOL_TICKER, SUSDS_TICKER, SWISE_TICKER],
    GNOSIS: [ETH_TICKER, BTC_TICKER, SDAI_TICKER, BCSPX_TICKER],
}

BTC_WALLET_PRIVATE_KEY: str = config('BTC_WALLET_PRIVATE_KEY', default='')
SOL_WALLET_PRIVATE_KEY: str = config('SOL_WALLET_PRIVATE_KEY', default='')  # eth
SUSDS_WALLET_PRIVATE_KEY: str = config('SUSDS_WALLET_PRIVATE_KEY', default='')  # eth
SWISE_WALLET_PRIVATE_KEY: str = config('SWISE_WALLET_PRIVATE_KEY', default='')  # eth
ETH_WALLET_PRIVATE_KEY: str = config('ETH_WALLET_PRIVATE_KEY', default='')  # gno
SDAI_WALLET_PRIVATE_KEY: str = config('SDAI_WALLET_PRIVATE_KEY', default='')  # gno
BCSPX_WALLET_PRIVATE_KEY: str = config('BCSPX_WALLET_PRIVATE_KEY', default='')  # gno

BTC_WALLET = get_hot_wallet_account(BTC_WALLET_PRIVATE_KEY)
SOL_WALLET = get_hot_wallet_account(SOL_WALLET_PRIVATE_KEY)
SUSDS_WALLET = get_hot_wallet_account(SUSDS_WALLET_PRIVATE_KEY)
SWISE_WALLET = get_hot_wallet_account(SWISE_WALLET_PRIVATE_KEY)
ETH_WALLET = get_hot_wallet_account(ETH_WALLET_PRIVATE_KEY)
SDAI_WALLET = get_hot_wallet_account(SDAI_WALLET_PRIVATE_KEY)
BCSPX_WALLET = get_hot_wallet_account(BCSPX_WALLET_PRIVATE_KEY)

BTC_VAULT: str = config('BTC_VAULT', default='')
SOL_VAULT: str = config('SOL_VAULT', default='')
SUSDS_VAULT: str = config('SUSDS_VAULT', default='')
SWISE_VAULT: str = config('SWISE_VAULT', default='')
ETH_VAULT: str = config('ETH_VAULT', default='')
SDAI_VAULT: str = config('SDAI_VAULT', default='')
BCSPX_VAULT: str = config('BCSPX_VAULT', default='')


TICKER_TO_SETTINGS: dict[str, tuple[LocalAccount | None, str]] = {
    BTC_TICKER: (BTC_WALLET, BTC_VAULT),
    SOL_TICKER: (SOL_WALLET, SOL_VAULT),
    SUSDS_TICKER: (SUSDS_WALLET, SUSDS_VAULT),
    SWISE_TICKER: (SWISE_WALLET, SWISE_VAULT),
    ETH_TICKER: (ETH_WALLET, ETH_VAULT),
    SDAI_TICKER: (SDAI_WALLET, SDAI_VAULT),
    BCSPX_TICKER: (BCSPX_WALLET, BCSPX_VAULT),
}

TOKEN_ADDRESSES = {
    MAINNET: {
        ETH_TICKER: Web3.to_checksum_address('0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE'),
        WETH_TICKER: Web3.to_checksum_address('0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2'),
        BTC_TICKER: Web3.to_checksum_address('0x2260fac5e5542a773aa44fbcfedf7c193bc2c599'),
        SOL_TICKER: Web3.to_checksum_address('0xD31a59c85aE9D8edEFeC411D448f90841571b89c'),
        USDS_TICKER: Web3.to_checksum_address('0xdC035D45d973E3EC169d2276DDab16f1e407384F'),
        SUSDS_TICKER: Web3.to_checksum_address('0xa3931d71877c0e7a3148cb7eb4463524fec27fbd'),
        SWISE_TICKER: Web3.to_checksum_address('0x48c3399719b582dd63eb5aadf12a40b4c3f52fa2'),
    },
    GNOSIS: {
        DAI_TICKER: Web3.to_checksum_address('0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE'),
        GNO_TICKER: Web3.to_checksum_address('0x9C58BAcC331c9aa871AFD802DB6379a98e80CEdb'),
        ETH_TICKER: Web3.to_checksum_address('0x6A023CCd1ff6F2045C3309768eAd9E68F978f6e1'),
        BTC_TICKER: Web3.to_checksum_address('0x8e5bbbb09ed1ebde8674cda39a0c169401db4252'),
        SDAI_TICKER: Web3.to_checksum_address('0xaf204776c7245bF4147c2612BF6e5972Ee483701'),
        BCSPX_TICKER: Web3.to_checksum_address('0x1e2C4fb7eDE391d116E6B41cD0608260e8801D59'),
    },
}
NETWORK_BASE_TICKERS = {
    MAINNET: ETH_TICKER,
    GNOSIS: GNO_TICKER,
}

NETWORK_BASE_TICKER_ADDRESSES = {  # vault base
    MAINNET: TOKEN_ADDRESSES[MAINNET][ETH_TICKER],
    GNOSIS: TOKEN_ADDRESSES[GNOSIS][GNO_TICKER],
}

MIN_ETH_FOR_GAS_AMOUNT = Web3.to_wei(0.01, 'ether')

COWSWAP_REQUEST_TIMEOUT: int = config('COWSWAP_REQUEST_TIMEOUT', default='60', cast=int)
COWSWAP_ORDER_PROCESSING_TIMEOUT: int = config(
    'COWSWAP_ORDER_PROCESSING_TIMEOUT', default='60', cast=int
)
