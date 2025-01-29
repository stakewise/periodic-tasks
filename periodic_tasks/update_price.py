import logging

from periodic_tasks.common.sentry import setup_sentry
from periodic_tasks.price.tasks import check_and_sync

logger = logging.getLogger(__name__)


setup_sentry()
check_and_sync()
