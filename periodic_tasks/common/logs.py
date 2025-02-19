import logging

from gql.transport.aiohttp import log as requests_logger


def setup_logging() -> None:
    """Setup logging for the project"""
    logging.basicConfig(level=logging.INFO)
    requests_logger.setLevel(logging.WARNING)
