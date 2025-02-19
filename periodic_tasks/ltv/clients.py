import logging

from sw_utils.graph.client import GraphClient

from periodic_tasks.common.clients import get_execution_client, hot_wallet_account
from periodic_tasks.common.settings import (
    EXECUTION_ENDPOINT,
    GRAPH_API_RETRY_TIMEOUT,
    GRAPH_API_TIMEOUT,
    GRAPH_API_URL,
    GRAPH_PAGE_SIZE,
)

logger = logging.getLogger(__name__)

execution_client = get_execution_client(EXECUTION_ENDPOINT, account=hot_wallet_account)


graph_client = GraphClient(
    endpoint=GRAPH_API_URL,
    request_timeout=GRAPH_API_TIMEOUT,
    retry_timeout=GRAPH_API_RETRY_TIMEOUT,
    page_size=GRAPH_PAGE_SIZE,
)
