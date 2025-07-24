from decimal import Decimal

from decouple import config
from web3 import Web3

# graph
GRAPH_API_URL: str = config('GRAPH_API_URL')
GRAPH_API_TIMEOUT: int = config('GRAPH_API_TIMEOUT', default='10', cast=int)
GRAPH_API_RETRY_TIMEOUT: int = config('GRAPH_API_RETRY_TIMEOUT', default='60', cast=int)

VAULTS: list[str] = config('VAULTS', cast=lambda x: x.split(','))

DRY_RUN: bool = config('DRY_RUN', default='False', cast=bool)

MULTICALL_BATCH_SIZE: int = config('MULTICALL_BATCH_SIZE', default='20', cast=int)

# Minimum amount of rewards to process reward splitter, measured in ETH.
REWARD_SPLITTER_MIN_ASSETS_ETH: Decimal = config(
    'REWARD_SPLITTER_MIN_ASSETS_ETH', default='0.001', cast=Decimal
)

REWARD_SPLITTER_MIN_ASSETS = Web3.to_wei(REWARD_SPLITTER_MIN_ASSETS_ETH, 'ether')
