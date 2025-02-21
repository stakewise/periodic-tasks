from decouple import config

from periodic_tasks.common.networks import NETWORKS

EXECUTION_ENDPOINT: str = config('EXECUTION_ENDPOINT', default='')
HOT_WALLET_PRIVATE_KEY: str = config('HOT_WALLET_PRIVATE_KEY', default='')

GRAPH_PAGE_SIZE: int = config('GRAPH_PAGE_SIZE', default=100, cast=int)


EXECUTION_TRANSACTION_TIMEOUT: int = config('EXECUTION_TRANSACTION_TIMEOUT', default=300, cast=int)

SENTRY_DSN: str = config('SENTRY_DSN', default='')

# Prometheus
METRICS_HOST: str = config('METRICS_HOST', default='127.0.0.1')
METRICS_PORT: int = config('METRICS_PORT', default=9100, cast=int)
METRICS_REFRESH_INTERNAL: int = config('METRICS_REFRESH_INTERNAL', default=60 * 5, cast=int)

# gas settings
ATTEMPTS_WITH_DEFAULT_GAS: int = config('ATTEMPTS_WITH_DEFAULT_GAS', default=3, cast=int)
MAX_FEE_PER_GAS_GWEI: int = config('MAX_FEE_PER_GAS_GWEI', default=100, cast=int)
PRIORITY_FEE_NUM_BLOCKS: int = config('PRIORITY_FEE_NUM_BLOCKS', default=10, cast=int)
PRIORITY_FEE_PERCENTILE: float = config('PRIORITY_FEE_PERCENTILE', default=80.0, cast=float)

NETWORK = config('NETWORK')
network_config = NETWORKS[NETWORK]
