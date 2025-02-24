import logging

from eth_account import Account
from eth_account.signers.local import LocalAccount
from web3 import AsyncWeb3, Web3
from web3.middleware.signing import async_construct_sign_and_send_raw_middleware

from periodic_tasks.common.settings import EXECUTION_ENDPOINT, HOT_WALLET_PRIVATE_KEY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_execution_client(endpoint: str = EXECUTION_ENDPOINT) -> AsyncWeb3:
    client = AsyncWeb3(Web3.AsyncHTTPProvider(endpoint))
    return client


async def setup_execution_client(client: AsyncWeb3, account: LocalAccount) -> AsyncWeb3:
    """Setup Web3 private key"""
    client.middleware_onion.add(await async_construct_sign_and_send_raw_middleware(account))
    client.eth.default_account = account.address
    return client


def get_hot_wallet_account(private_key: str | None) -> LocalAccount | None:
    if private_key:
        return Account().from_key(private_key)
    return None


hot_wallet_account = get_hot_wallet_account(HOT_WALLET_PRIVATE_KEY)
if hot_wallet_account:
    logger.info('Wallet address: %s', hot_wallet_account.address)
