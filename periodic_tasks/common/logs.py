import logging.config

LOG_LEVEL = 'INFO'
GQL_LOG_LEVEL = 'WARNING'


def setup_logging() -> None:
    logging.config.dictConfig(
        {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'simple': {
                    'format': '%(asctime)s %(levelname)-8s %(name)s - %(message)s',
                    'datefmt': '%Y-%m-%d %H:%M:%S',
                }
            },
            'handlers': {'stdout': {'class': 'logging.StreamHandler', 'formatter': 'simple'}},
            'loggers': {
                'src': {'propagate': False, 'level': LOG_LEVEL, 'handlers': ['stdout']},
                'gql.transport.aiohttp': {
                    'propagate': False,
                    'level': GQL_LOG_LEVEL,
                    'handlers': ['stdout'],
                },
            },
            'root': {'level': LOG_LEVEL, 'handlers': ['stdout']},
        }
    )
