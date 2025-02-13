import logging

from eth_typing import ChecksumAddress
from web3 import Web3
from web3.types import Wei

from periodic_tasks.common.settings import EXECUTION_TRANSACTION_TIMEOUT

from .clients import execution_client
from .contracts import token_distributor_contract

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Function to get current ETH balance
def get_eth_balance(address: ChecksumAddress) -> Wei:
    return Web3.eth.get_balance(address)


async def distribute_tokens(
    token: ChecksumAddress, amount: Wei, vault_address: ChecksumAddress
) -> None:
    tx = token_distributor_contract.distribute_one_time(
        token=token, amount=amount, vault=vault_address
    )
    logger.info('Distribution transaction sent, tx hash: %s', tx.hex())

    # Wait for tx receipt
    logger.info('Waiting for tx receipt')
    receipt = execution_client.eth.wait_for_transaction_receipt(
        tx, timeout=EXECUTION_TRANSACTION_TIMEOUT
    )

    # Check receipt status
    if not receipt['status']:
        raise RuntimeError(f'Update tx failed, tx hash: {tx.hex()}')
    logger.info('Tx confirmed')
