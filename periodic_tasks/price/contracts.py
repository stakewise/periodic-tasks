from periodic_tasks.common.contracts import ContractWrapper
from periodic_tasks.price.clients import (
    sender_execution_client,
    target_execution_client,
)
from periodic_tasks.price.settings import price_network_config


class PriceFeedContract(ContractWrapper):
    pass


class PriceFeedSenderContract(ContractWrapper):
    pass


target_price_feed_contract = PriceFeedContract(
    address=price_network_config.TARGET_PRICE_FEED_CONTRACT_ADDRESS,
    abi_path='abi/IPriceFeed.json',
    client=target_execution_client,
)
price_feed_sender_contract = PriceFeedSenderContract(
    address=price_network_config.PRICE_FEED_SENDER_CONTRACT_ADDRESS,
    abi_path='abi/IPriceFeedSender.json',
    client=sender_execution_client,
)
