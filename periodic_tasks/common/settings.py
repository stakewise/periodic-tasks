from decouple import config

from periodic_tasks.common.networks import NETWORKS

EXECUTION_ENDPOINT: str = config('EXECUTION_ENDPOINT', default='')
HOT_WALLET_PRIVATE_KEY: str = config('HOT_WALLET_PRIVATE_KEY', default='')

GRAPH_PAGE_SIZE: int = config('GRAPH_PAGE_SIZE', default=100, cast=int)


EXECUTION_TRANSACTION_TIMEOUT: int = config('EXECUTION_TRANSACTION_TIMEOUT', default=300, cast=int)

SENTRY_DSN: str = config('SENTRY_DSN', default='')

NETWORK = config('NETWORK')
network_config = NETWORKS[NETWORK]
