import logging

import gql
from gql.transport.requests import RequestsHTTPTransport

from src.common.clients import get_execution_client, hot_wallet_account
from src.common.settings import EXECUTION_ENDPOINT

from .settings import GRAPH_API_TIMEOUT, GRAPH_API_URL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

execution_client = get_execution_client(EXECUTION_ENDPOINT, account=hot_wallet_account)


def get_graph_client() -> gql.Client:
    transport = RequestsHTTPTransport(
        url=GRAPH_API_URL,
        timeout=GRAPH_API_TIMEOUT,
    )
    return gql.Client(transport=transport)


graph_client = get_graph_client()
