from decouple import config

sender_execution_endpoint: str = config('SENDER_EXECUTION_ENDPOINT')
target_execution_endpoint: str = config('TARGET_EXECUTION_ENDPOINT')
