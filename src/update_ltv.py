import logging
import sys

from src.ltv.tasks import update_vault_max_ltv_user

logger = logging.getLogger(__name__)

try:
    update_vault_max_ltv_user()
except Exception as e:
    logger.error(e)
    sys.exit(1)
