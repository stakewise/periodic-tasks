import logging

from sw_utils.graph.client import GraphClient

from periodic_tasks.common.settings import GRAPH_PAGE_SIZE

from .settings import GRAPH_API_RETRY_TIMEOUT, GRAPH_API_TIMEOUT, GRAPH_API_URL

logger = logging.getLogger(__name__)


graph_client = GraphClient(
    endpoint=GRAPH_API_URL,
    request_timeout=GRAPH_API_TIMEOUT,
    retry_timeout=GRAPH_API_RETRY_TIMEOUT,
    page_size=GRAPH_PAGE_SIZE,
)
