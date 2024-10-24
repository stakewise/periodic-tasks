# type: ignore
import logging
import os
import sys
import time

from dotenv import load_dotenv
from eth_account import Account
from web3 import Web3
from web3.middleware import construct_sign_and_send_raw_middleware

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TWELVE_HOURS = 12 * 60 * 60
ONE_HOUR = 60 * 60
CHECK_INTERVAL = 60  # Check every minute

MAINNET_PROVIDER = Web3(Web3.HTTPProvider(os.getenv('EXECUTION_ENDPOINT')))
TARGET_RPC_PROVIDER = Web3(Web3.HTTPProvider(os.getenv('TARGET_RPC_URL')))
HOT_WALLET_PRIVATE_KEY = os.getenv('HOT_WALLET_PRIVATE_KEY')
ACCOUNT = Account().from_key(HOT_WALLET_PRIVATE_KEY)
ACCOUNT_ADDRESS = ACCOUNT.address
MAINNET_PROVIDER.middleware_onion.add(construct_sign_and_send_raw_middleware(ACCOUNT))

price_feed_abi = [
    {
        'constant': True,
        'inputs': [],
        'name': 'latestTimestamp',
        'outputs': [{'name': '', 'type': 'uint256'}],
        'payable': False,
        'stateMutability': 'view',
        'type': 'function',
    },
    {
        'constant': False,
        'inputs': [
            {'name': 'targetChain', 'type': 'uint16'},
            {'name': 'targetAddress', 'type': 'address'},
        ],
        'name': 'syncRate',
        'outputs': [],
        'payable': True,
        'stateMutability': 'payable',
        'type': 'function',
    },
    {
        'constant': True,
        'inputs': [{'name': 'targetChain', 'type': 'uint16'}],
        'name': 'quoteRateSync',
        'outputs': [{'name': 'cost', 'type': 'uint256'}],
        'payable': False,
        'stateMutability': 'view',
        'type': 'function',
    },
]

price_feed_address = Web3.to_checksum_address(os.getenv('PRICE_FEED'))
price_feed_sender_address = Web3.to_checksum_address(os.getenv('PRICE_FEED_SENDER'))
target_chain = int(os.getenv('TARGET_CHAIN'))
target_address = Web3.to_checksum_address(os.getenv('TARGET_ADDRESS'))


def check_and_sync():
    price_feed = TARGET_RPC_PROVIDER.eth.contract(address=price_feed_address, abi=price_feed_abi)
    price_feed_sender = MAINNET_PROVIDER.eth.contract(
        address=price_feed_sender_address, abi=price_feed_abi
    )

    # Step 1: Check latest timestamp
    latest_timestamp = price_feed.functions.latestTimestamp().call()
    current_time = int(time.time())

    if current_time - latest_timestamp < TWELVE_HOURS:
        logger.info('Less than 12 hours since the last update. No action needed.')
        return

    # Step 2: Get the cost
    current_rate = price_feed_sender.functions.quoteRateSync(target_chain).call()

    # Step 3: Sync the rate
    tx = price_feed_sender.functions.syncRate(target_chain, target_address).transact(
        {
            'from': ACCOUNT_ADDRESS,
            'value': current_rate,
        }
    )

    logger.info('Sync transaction sent: %s', tx.hex())
    receipt = MAINNET_PROVIDER.eth.wait_for_transaction_receipt(tx)

    if not receipt['status']:
        raise RuntimeError(f'Sync transaction failed, tx hash: {tx.hex()}')

    logger.info('Sync transaction confirmed.')

    # Step 4: Wait for the timestamp to update on the target chain
    start_time = int(time.time())
    while int(time.time()) - start_time < ONE_HOUR:
        new_timestamp = price_feed.functions.latestTimestamp().call()
        if new_timestamp > latest_timestamp:
            logger.info('Timestamp updated on the target chain.')
            return
        logger.info('Waiting for the timestamp to update...')
        time.sleep(CHECK_INTERVAL)

    raise TimeoutError('Timestamp did not update on the target chain within one hour.')


if __name__ == '__main__':
    try:
        check_and_sync()
    except Exception as e:
        logger.error(e)
        sys.exit(1)
