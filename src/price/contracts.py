from src.common.contracts import ContractWrapper
from src.common.contracts import execution_client as sender_execution_client
from src.price.clients import target_execution_client
from src.price.settings import (
    price_feed_sender_contract_address,
    target_price_feed_contract_address,
)

ABI_DIR = 'src/price/abi'


class PriceFeedContract(ContractWrapper):
    pass


class PriceFeedSenderContract(ContractWrapper):
    pass


target_price_feed_contract = PriceFeedContract(
    address=target_price_feed_contract_address,
    abi_path=f'{ABI_DIR}/IPriceFeed.json',
    client=target_execution_client,
)
price_feed_sender_contract = PriceFeedSenderContract(
    address=price_feed_sender_contract_address,
    abi_path=f'{ABI_DIR}/IPriceFeedSender.json',
    client=sender_execution_client,
)
