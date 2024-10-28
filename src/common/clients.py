import logging

from eth_account import Account
from web3 import Web3
from web3.middleware import construct_sign_and_send_raw_middleware

from src.common.settings import EXECUTION_ENDPOINT, HOT_WALLET_PRIVATE_KEY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

hot_wallet_account = Account().from_key(HOT_WALLET_PRIVATE_KEY)
execution_client = Web3(Web3.HTTPProvider(EXECUTION_ENDPOINT))
execution_client.middleware_onion.add(construct_sign_and_send_raw_middleware(hot_wallet_account))
logger.info('Wallet address: %s', hot_wallet_account.address)
