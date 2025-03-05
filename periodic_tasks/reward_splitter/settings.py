from decouple import config
from web3 import Web3

# graph
GRAPH_API_URL: str = config('GRAPH_API_URL')
GRAPH_API_TIMEOUT: int = config('GRAPH_API_TIMEOUT', default='10', cast=int)
GRAPH_API_RETRY_TIMEOUT: int = config('GRAPH_API_RETRY_TIMEOUT', default='60', cast=int)

VAULTS: list[str] = config('VAULTS', cast=lambda x: x.split(','))

DRY_RUN: bool = config('DRY_RUN', default='False', cast=bool)

MULTICALL_BATCH_SIZE: int = config('MULTICALL_BATCH_SIZE', default='20', cast=int)

# Minimum amount of rewards to process reward splitter
REWARD_SPLITTER_MIN_ASSETS: int = config(
    'REWARD_SPLITTER_MIN_ASSETS', default=Web3.to_wei('0.001', 'ether'), cast=int
)
