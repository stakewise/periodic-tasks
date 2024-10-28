from decouple import config
from eth_typing import ChecksumAddress
from web3 import Web3

from src.common.networks import NETWORKS, Network

NETWORK: Network = config('NETWORK', cast=Network)
network_config = NETWORKS[NETWORK]

VAULT: ChecksumAddress = config('VAULT', cast=Web3.to_checksum_address)

# graph
GRAPH_API_URL: str = config('GRAPH_API_URL')
GRAPH_API_TIMEOUT: int = config('GRAPH_API_TIMEOUT', default='10', cast=int)
