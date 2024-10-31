from typing import cast

from decouple import config

from src.common.networks import PriceNetworkConfig
from src.common.settings import network_config

sender_execution_endpoint: str = config('SENDER_EXECUTION_ENDPOINT')
target_execution_endpoint: str = config('TARGET_EXECUTION_ENDPOINT')

price_network_config = cast(PriceNetworkConfig, network_config.PRICE_NETWORK_CONFIG)
