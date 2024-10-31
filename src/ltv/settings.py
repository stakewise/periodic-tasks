from decouple import config
from eth_typing import ChecksumAddress
from web3 import Web3

VAULT: ChecksumAddress = config('VAULT', cast=Web3.to_checksum_address)

# graph
GRAPH_API_URL: str = config('GRAPH_API_URL')
GRAPH_API_TIMEOUT: int = config('GRAPH_API_TIMEOUT', default='10', cast=int)
