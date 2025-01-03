import logging

from src.common.sentry import setup_sentry
from src.price.tasks import check_and_sync

logger = logging.getLogger(__name__)


setup_sentry()
check_and_sync()
