import logging

from periodic_tasks.common.clients import get_execution_client, hot_wallet_account
from periodic_tasks.common.settings import EXECUTION_ENDPOINT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

execution_client = get_execution_client(EXECUTION_ENDPOINT, account=hot_wallet_account)
