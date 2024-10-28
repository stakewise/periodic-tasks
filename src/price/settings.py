from decouple import config
from eth_typing import ChecksumAddress
from web3 import Web3

target_execution_endpoint: str = config('TARGET_EXECUTION_ENDPOINT')

# network config
target_price_feed_contract_address: ChecksumAddress = config(
    'TARGET_PRICE_FEED_CONTRACT_ADDRESS', cast=Web3.to_checksum_address
)
price_feed_sender_contract_address: ChecksumAddress = config(
    'PRICE_FEED_SENDER_CONTRACT_ADDRESS', cast=Web3.to_checksum_address
)
target_chain: int = config('TARGET_CHAIN', cast=int)
target_address: ChecksumAddress = config('TARGET_ADDRESS', cast=Web3.to_checksum_address)
