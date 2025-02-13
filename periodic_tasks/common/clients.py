import logging

from eth_account import Account
from eth_account.signers.local import LocalAccount
from web3 import Web3
from web3.middleware import construct_sign_and_send_raw_middleware

from periodic_tasks.common.settings import HOT_WALLET_PRIVATE_KEY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_execution_client(endpoint: str, account: LocalAccount | None = None) -> Web3:
    client = Web3(Web3.HTTPProvider(endpoint))
    if account:
        client.middleware_onion.add(construct_sign_and_send_raw_middleware(account))
        client.eth.default_account = account.address
    return client


hot_wallet_account = Account().from_key(HOT_WALLET_PRIVATE_KEY)
logger.info('Wallet address: %s', hot_wallet_account.address)
