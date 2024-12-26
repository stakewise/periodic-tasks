import asyncio
import logging
import sys

from src.common.logs import setup_gql_log_level
from src.common.sentry import setup_sentry
from src.ltv.tasks import update_vault_max_ltv_user

logger = logging.getLogger(__name__)


async def main() -> None:
    await update_vault_max_ltv_user()


try:
    setup_sentry()
    setup_gql_log_level()
    asyncio.run(main())
except Exception as e:
    logger.error(e)
    sys.exit(1)
