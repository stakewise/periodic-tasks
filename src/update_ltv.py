import logging
import sys

from src.common.logs import setup_gql_log_level
from src.ltv.tasks import update_vault_max_ltv_user

logger = logging.getLogger(__name__)

try:
    setup_gql_log_level()
    update_vault_max_ltv_user()
except Exception as e:
    logger.error(e)
    sys.exit(1)
