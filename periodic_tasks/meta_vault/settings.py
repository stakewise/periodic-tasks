from decouple import config
from eth_typing import ChecksumAddress
from web3 import Web3
from web3.types import Wei

# graph
GRAPH_API_URL: str = config('GRAPH_API_URL')
GRAPH_API_TIMEOUT: int = config('GRAPH_API_TIMEOUT', default='10', cast=int)
GRAPH_API_RETRY_TIMEOUT: int = config('GRAPH_API_RETRY_TIMEOUT', default='60', cast=int)

# Metavaults
META_VAULTS: list[ChecksumAddress] = config(
    'META_VAULTS', cast=lambda x: [Web3.to_checksum_address(vault) for vault in x.split(',')]
)

MIN_ACTIVATION_BALANCE = Web3.to_wei(32, 'ether')

META_VAULT_MIN_DEPOSIT_AMOUNT: Wei = config(
    'META_VAULT_MIN_DEPOSIT_AMOUNT', default=MIN_ACTIVATION_BALANCE, cast=int
)
