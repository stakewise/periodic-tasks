from web3 import Web3

from src.price.settings import target_execution_endpoint

target_execution_client = Web3(Web3.HTTPProvider(target_execution_endpoint))
