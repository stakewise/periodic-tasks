import logging

from sw_utils.graph.client import GraphClient

from src.common.clients import get_execution_client, hot_wallet_account
from src.common.settings import EXECUTION_ENDPOINT, GRAPH_PAGE_SIZE

from .settings import GRAPH_API_RETRY_TIMEOUT, GRAPH_API_TIMEOUT, GRAPH_API_URL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

execution_client = get_execution_client(EXECUTION_ENDPOINT, account=hot_wallet_account)

graph_client = GraphClient(
    endpoint=GRAPH_API_URL,
    request_timeout=GRAPH_API_TIMEOUT,
    retry_timeout=GRAPH_API_RETRY_TIMEOUT,
    page_size=GRAPH_PAGE_SIZE,
)
