import asyncio

from periodic_tasks.common.logs import setup_logging
from periodic_tasks.common.sentry import setup_sentry
from periodic_tasks.exit.tasks import force_exits


async def main() -> None:
    await force_exits()


setup_logging()
setup_sentry()
asyncio.run(main())
