from src.common.clients import get_execution_client, hot_wallet_account
from src.price.settings import sender_execution_endpoint, target_execution_endpoint

sender_execution_client = get_execution_client(
    sender_execution_endpoint, account=hot_wallet_account
)
target_execution_client = get_execution_client(target_execution_endpoint)
