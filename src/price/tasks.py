import logging
import time
from datetime import timedelta

from src.common.settings import price_network_config
from src.price.clients import hot_wallet_account, sender_execution_client
from src.price.contracts import price_feed_sender_contract, target_price_feed_contract

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# How long to wait since the last update before we can run another update
UPDATE_INTERVAL = timedelta(hours=12)

# How long to wait for update on the target chain
MAX_WAITING_TIME = timedelta(hours=1)

# How often to check target chain for updates
CHECK_INTERVAL = timedelta(minutes=1)


def check_and_sync() -> None:
    # Step 1: Check latest timestamp
    latest_timestamp = target_price_feed_contract.functions.latestTimestamp().call()
    current_time = int(time.time())
    update_interval_sec = UPDATE_INTERVAL.total_seconds()

    if current_time - latest_timestamp < update_interval_sec:
        logger.info(
            'Less than %d hours since the last update. No action needed.',
            update_interval_sec // 3600,
        )
        return

    # Step 2: Get the cost
    target_chain = price_network_config.TARGET_CHAIN
    target_address = price_network_config.TARGET_ADDRESS

    current_rate = price_feed_sender_contract.functions.quoteRateSync(target_chain).call()

    # Step 3: Sync the rate
    tx = price_feed_sender_contract.functions.syncRate(target_chain, target_address).transact(
        {
            'from': hot_wallet_account.address,
            'value': current_rate,
        }
    )

    logger.info('Sync transaction sent: %s', tx.hex())
    receipt = sender_execution_client.eth.wait_for_transaction_receipt(tx)

    if not receipt['status']:
        raise RuntimeError(f'Sync transaction failed, tx hash: {tx.hex()}')

    logger.info('Sync transaction confirmed.')

    # Step 4: Wait for the timestamp to update on the target chain
    start_time = int(time.time())
    check_interval_sec = int(CHECK_INTERVAL.total_seconds())
    max_waiting_time_sec = int(MAX_WAITING_TIME.total_seconds())

    while int(time.time()) - start_time < max_waiting_time_sec:
        new_timestamp = target_price_feed_contract.functions.latestTimestamp().call()
        if new_timestamp > latest_timestamp:
            logger.info('Timestamp updated on the target chain.')
            return
        logger.info('Waiting for the timestamp to update...')
        time.sleep(check_interval_sec)

    raise TimeoutError(
        f'Timestamp did not update on the target chain within {check_interval_sec} sec.'
    )
