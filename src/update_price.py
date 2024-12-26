import logging
import sys

from src.common.sentry import setup_sentry
from src.price.tasks import check_and_sync

logger = logging.getLogger(__name__)


try:
    setup_sentry()
    check_and_sync()
except Exception as e:
    logger.error(e)
    sys.exit(1)
