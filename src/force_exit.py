import logging
import sys

from src.exit.tasks import force_exits

logger = logging.getLogger(__name__)

try:
    force_exits()
except Exception as e:
    logger.exception(e)
    sys.exit(1)
