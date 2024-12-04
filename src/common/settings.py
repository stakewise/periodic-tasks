from decouple import config

from src.common.networks import NETWORKS, Network

EXECUTION_ENDPOINT: str = config('EXECUTION_ENDPOINT', default='')
HOT_WALLET_PRIVATE_KEY: str = config('HOT_WALLET_PRIVATE_KEY')


EXECUTION_TRANSACTION_TIMEOUT: int = config('EXECUTION_TRANSACTION_TIMEOUT', default=300, cast=int)


NETWORK: Network = config('NETWORK', cast=Network)
network_config = NETWORKS[NETWORK]
