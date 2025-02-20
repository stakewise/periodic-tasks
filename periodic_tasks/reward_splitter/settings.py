from decouple import config

# graph
GRAPH_API_URL: str = config('GRAPH_API_URL')
GRAPH_API_TIMEOUT: int = config('GRAPH_API_TIMEOUT', default='10', cast=int)
GRAPH_API_RETRY_TIMEOUT: int = config('GRAPH_API_RETRY_TIMEOUT', default='60', cast=int)

VAULTS: list[str] = config('VAULTS', cast=lambda x: x.split(','))

DRY_RUN: bool = config('DRY_RUN', default='False', cast=bool)
