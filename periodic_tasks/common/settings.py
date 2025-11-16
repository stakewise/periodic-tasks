from decouple import config
from web3 import Web3
from web3.types import Gwei, Wei

from periodic_tasks.common.networks import NETWORKS

EXECUTION_ENDPOINT: str = config('EXECUTION_ENDPOINT', default='')
HOT_WALLET_PRIVATE_KEY: str = config('HOT_WALLET_PRIVATE_KEY', default='')

# graph
GRAPH_API_URL: str = config('GRAPH_API_URL', default='')
GRAPH_API_TIMEOUT: int = config('GRAPH_API_TIMEOUT', default='10', cast=int)
GRAPH_API_RETRY_TIMEOUT: int = config('GRAPH_API_RETRY_TIMEOUT', default='60', cast=int)
GRAPH_PAGE_SIZE: int = config('GRAPH_PAGE_SIZE', default=100, cast=int)


EXECUTION_TRANSACTION_TIMEOUT: int = config('EXECUTION_TRANSACTION_TIMEOUT', default=300, cast=int)

SENTRY_DSN: str = config('SENTRY_DSN', default='')

# Prometheus
METRICS_HOST: str = config('METRICS_HOST', default='127.0.0.1')
METRICS_PORT: int = config('METRICS_PORT', default=9100, cast=int)
METRICS_REFRESH_INTERNAL: int = config('METRICS_REFRESH_INTERNAL', default=60 * 5, cast=int)

# gas settings
ATTEMPTS_WITH_DEFAULT_GAS: int = config('ATTEMPTS_WITH_DEFAULT_GAS', default=3, cast=int)
MAX_FEE_PER_GAS_GWEI: Gwei = config('MAX_FEE_PER_GAS_GWEI', default=100, cast=int)
MAX_FEE_PER_GAS: Wei = Web3.to_wei(MAX_FEE_PER_GAS_GWEI, 'gwei')
PRIORITY_FEE_NUM_BLOCKS: int = config('PRIORITY_FEE_NUM_BLOCKS', default=10, cast=int)
PRIORITY_FEE_PERCENTILE: float = config('PRIORITY_FEE_PERCENTILE', default=80.0, cast=float)

NETWORK = config('NETWORK')
network_config = NETWORKS[NETWORK]

EVENTS_BLOCKS_RANGE_INTERVAL = config(
    'EVENTS_BLOCKS_RANGE_INTERVAL',
    default=43200 // network_config.SECONDS_PER_BLOCK,  # 12 hrs
    cast=int,
)
