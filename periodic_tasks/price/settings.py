from typing import cast

from decouple import config

from periodic_tasks.common.networks import PRICE_NETWORKS, PriceNetworkConfig
from periodic_tasks.common.settings import NETWORK

sender_execution_endpoint: str = config('SENDER_EXECUTION_ENDPOINT')
target_execution_endpoint: str = config('TARGET_EXECUTION_ENDPOINT')

price_network_config = cast(PriceNetworkConfig, PRICE_NETWORKS[NETWORK])
