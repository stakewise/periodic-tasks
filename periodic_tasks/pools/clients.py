import logging

from eth_account.signers.local import LocalAccount
from web3 import Web3

from periodic_tasks.common.clients import get_execution_client
from periodic_tasks.common.settings import EXECUTION_ENDPOINT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

execution_client = get_execution_client(EXECUTION_ENDPOINT)


def get_account_execution_client(account: LocalAccount) -> Web3:
    return get_execution_client(EXECUTION_ENDPOINT, account=account)
