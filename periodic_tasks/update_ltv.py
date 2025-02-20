import asyncio
import logging

from periodic_tasks.common.clients import hot_wallet_account, setup_execution_client
from periodic_tasks.common.logs import setup_gql_log_level
from periodic_tasks.common.sentry import setup_sentry
from periodic_tasks.ltv.clients import execution_client
from periodic_tasks.ltv.tasks import update_vault_max_ltv_user

logger = logging.getLogger(__name__)


async def main() -> None:
    if not hot_wallet_account:
        raise ValueError('Set HOT_WALLET_PRIVATE_KEY environment variable')
    await setup_execution_client(execution_client, hot_wallet_account)
    await update_vault_max_ltv_user()


setup_sentry()
setup_gql_log_level()
asyncio.run(main())
