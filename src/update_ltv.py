import logging
import sys

from src.common.sentry import setup_sentry
from src.ltv.tasks import update_vault_max_ltv_user

logger = logging.getLogger(__name__)

try:
    setup_sentry()
    update_vault_max_ltv_user()
except Exception as e:
    logger.error(e)
    sys.exit(1)
