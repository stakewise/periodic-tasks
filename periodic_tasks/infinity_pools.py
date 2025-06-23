import asyncio
import logging

from periodic_tasks.common.logs import setup_gql_log_level
from periodic_tasks.common.sentry import setup_sentry
from periodic_tasks.common.settings import NETWORK
from periodic_tasks.pools.settings import SUPPORTED_NETWORKS
from periodic_tasks.pools.tasks import handle_pools

logger = logging.getLogger(__name__)


async def main() -> None:
    if NETWORK not in SUPPORTED_NETWORKS:
        raise ValueError(f'Infinity pools assets swap in network {NETWORK} is not supported')

    await handle_pools()


setup_sentry()
setup_gql_log_level()
asyncio.run(main())
