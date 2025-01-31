import asyncio
import time

from prometheus_client import Gauge, Info, start_http_server
from sw_utils import InterruptHandler

from periodic_tasks import _get_project_meta
from periodic_tasks.common.logs import setup_gql_log_level
from periodic_tasks.common.sentry import setup_sentry
from periodic_tasks.common.settings import (
    METRICS_HOST,
    METRICS_PORT,
    METRICS_REFRESH_INTERNAL,
    NETWORK,
)
from periodic_tasks.exit.clients import execution_client
from periodic_tasks.exit.tasks import (
    fetch_leverage_positions,
    fetch_ostoken_exit_requests,
)
from periodic_tasks.ltv.tasks import get_max_ltv_users

RECORDS_LIMIT = 100


class Metrics:
    def __init__(self) -> None:
        self.app_version = Info('app_version', 'V3 Keeper version')
        self.execution_block = Gauge('execution_block', 'Chain finalized head: Execution Block')

        self.max_ltv_user = Gauge(
            'max_ltv_user',
            'Vault max ltv user',
            labelnames=['network', 'user', 'vault'],
        )

        self.ostoken_exit_request = Gauge(
            'ostoken_exit_request',
            'OStoken exit requests',
            labelnames=['network', 'user', 'vault'],
        )

        self.leverage_position = Gauge(
            'leverage_position',
            'Risky leverage positions',
            labelnames=['network', 'user', 'vault'],
        )

    def set_app_version(self) -> None:
        self.app_version.info({'version': _get_project_meta()['version']})


metrics = Metrics()
metrics.set_app_version()


async def liquidation_metrics() -> None:
    block = execution_client.eth.get_block('finalized')
    block_number = block['number']
    metrics.execution_block.set(block_number)

    exit_requests = await fetch_ostoken_exit_requests(block_number)
    for exit_request in exit_requests[:RECORDS_LIMIT]:
        metrics.ostoken_exit_request.labels(
            network=NETWORK, user=exit_request.owner, vault=exit_request.vault
        ).set(exit_request.ltv)

    leverage_positions = await fetch_leverage_positions(block_number)
    for leverage_position in leverage_positions[:RECORDS_LIMIT]:
        metrics.leverage_position.labels(
            network=NETWORK, user=leverage_position.user, vault=leverage_position.vault
        ).set(leverage_position.borrow_ltv)

    max_ltv_users = await get_max_ltv_users()
    for max_ltv_user in max_ltv_users[:RECORDS_LIMIT]:
        metrics.max_ltv_user.labels(
            network=NETWORK, user=max_ltv_user.address, vault=max_ltv_user.vault
        ).set(max_ltv_user.ltv)


async def main() -> None:
    await metrics_server()

    with InterruptHandler() as interrupt_handler:
        while not interrupt_handler.exit:
            start_time = time.time()
            await liquidation_metrics()
            sleep_time = max(METRICS_REFRESH_INTERNAL - (time.time() - start_time), 0)
            await interrupt_handler.sleep(sleep_time)


async def metrics_server() -> None:
    start_http_server(METRICS_PORT, METRICS_HOST)


if __name__ == '__main__':
    setup_sentry()
    setup_gql_log_level()
    asyncio.run(main())
