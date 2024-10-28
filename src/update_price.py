import logging
import sys

from src.price.tasks import check_and_sync

logger = logging.getLogger(__name__)


try:
    check_and_sync()
except Exception as e:
    logger.error(e)
    sys.exit(1)
