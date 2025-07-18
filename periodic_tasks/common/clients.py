import logging

from eth_account import Account
from eth_account.signers.local import LocalAccount
from web3 import AsyncWeb3, Web3
from web3.middleware.signing import async_construct_sign_and_send_raw_middleware

from periodic_tasks.common.settings import EXECUTION_ENDPOINT, HOT_WALLET_PRIVATE_KEY

logger = logging.getLogger(__name__)


def get_execution_client(endpoint: str = EXECUTION_ENDPOINT) -> AsyncWeb3:
    client = AsyncWeb3(Web3.AsyncHTTPProvider(endpoint))
    return client


async def setup_execution_client(w3: AsyncWeb3, account: LocalAccount) -> None:
    """Setup Web3 private key"""
    logger.info('Wallet address: %s', account.address)
    w3.middleware_onion.add(await async_construct_sign_and_send_raw_middleware(account))
    w3.eth.default_account = account.address


def get_hot_wallet_account(private_key: str | None) -> LocalAccount | None:
    if private_key:
        return Account().from_key(private_key)
    return None


hot_wallet_account = get_hot_wallet_account(HOT_WALLET_PRIVATE_KEY)

execution_client = get_execution_client()
