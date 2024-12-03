import logging
import sys

from src.common.logs import setup_gql_log_level
from src.exit.tasks import force_exits

logger = logging.getLogger(__name__)

try:
    setup_gql_log_level()
    force_exits()
except Exception as e:
    logger.exception(e)
    sys.exit(1)
