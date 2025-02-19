from periodic_tasks.common.logs import setup_logging
from periodic_tasks.common.sentry import setup_sentry
from periodic_tasks.price.tasks import check_and_sync

setup_logging()
setup_sentry()
check_and_sync()
