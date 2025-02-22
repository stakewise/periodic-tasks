from decouple import config
from sw_utils import ETH_NETWORKS

LTV_PERCENT_DELTA: float = config('LTV_PERCENT_DELTA', default='0.0002', cast=float)

# graph
GRAPH_API_URL: str = config('GRAPH_API_URL')
GRAPH_API_TIMEOUT: int = config('GRAPH_API_TIMEOUT', default='10', cast=int)
GRAPH_API_RETRY_TIMEOUT: int = config('GRAPH_API_RETRY_TIMEOUT', default='60', cast=int)

SUPPORTED_NETWORKS = ETH_NETWORKS
