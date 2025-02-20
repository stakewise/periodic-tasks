from periodic_tasks.common.clients import get_execution_client
from periodic_tasks.price.settings import (
    sender_execution_endpoint,
    target_execution_endpoint,
)

sender_execution_client = get_execution_client(sender_execution_endpoint)
target_execution_client = get_execution_client(target_execution_endpoint)
