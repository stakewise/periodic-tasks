import asyncio
import logging

from periodic_tasks.common.logs import setup_gql_log_level
from periodic_tasks.common.sentry import setup_sentry
from periodic_tasks.ltv.tasks import update_vault_max_ltv_user

logger = logging.getLogger(__name__)


async def main() -> None:
    await update_vault_max_ltv_user()


setup_sentry()
setup_gql_log_level()
asyncio.run(main())
