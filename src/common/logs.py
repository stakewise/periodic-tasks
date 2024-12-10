import logging

from gql.transport.requests import log as requests_logger


def setup_gql_log_level() -> None:
    """Raise GQL default log level"""
    requests_logger.setLevel(logging.WARNING)
