import asyncio
import logging
import sys

from src.ltv.tasks import get_vault_max_ltv

logger = logging.getLogger(__name__)

try:
    asyncio.run(get_vault_max_ltv())
except Exception as e:
    logger.error(e)
    sys.exit(1)
