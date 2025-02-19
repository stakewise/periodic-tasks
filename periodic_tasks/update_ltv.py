import asyncio

from periodic_tasks.common.logs import setup_logging
from periodic_tasks.common.sentry import setup_sentry
from periodic_tasks.ltv.tasks import update_vault_max_ltv_user


async def main() -> None:
    await update_vault_max_ltv_user()


setup_logging()
setup_sentry()
asyncio.run(main())
