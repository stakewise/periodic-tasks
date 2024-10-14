from decouple import Csv, config
from web3 import Web3

from .networks import NETWORKS, Network

NETWORK = config('NETWORK', cast=Network)
EXECUTION_ENDPOINT = config('EXECUTION_ENDPOINT')
HOT_WALLET_PRIVATE_KEY = config('HOT_WALLET_PRIVATE_KEY')

VAULT = config('VAULT', cast=Web3.to_checksum_address)

# graph
GRAPH_API_URL = config('GRAPH_API_URL')
GRAPH_API_TIMEOUT = config('GRAPH_API_TIMEOUT', default='10', cast=int)

# IPFS
IPFS_FETCH_ENDPOINTS = config(
    'IPFS_FETCH_ENDPOINTS',
    cast=Csv(),
    default=','.join(
        ['https://stakewise-v3.infura-ipfs.io', 'https://gateway.pinata.cloud', 'https://ipfs.io']
    ),
)

IPFS_FETCH_CLIENT_TIMEOUT = config('IPFS_FETCH_CLIENT_TIMEOUT', default='60', cast=int)

network_config = NETWORKS[NETWORK]
