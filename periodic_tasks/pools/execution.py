import logging

from eth_account.signers.local import LocalAccount
from eth_typing import ChecksumAddress
from web3.types import Wei

from periodic_tasks.common.settings import EXECUTION_TRANSACTION_TIMEOUT

from .clients import execution_client, get_account_execution_client
from .contracts import get_erc20_contract, token_distributor_contract

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
        raise RuntimeError(f'Distribution tx failed, tx hash: {tx.hex()}')
    logger.info('Tx confirmed')


def approve_spending(
    address: ChecksumAddress, token: ChecksumAddress, wallet: LocalAccount
) -> None:
    contract = get_erc20_contract(address=token, client=get_account_execution_client(wallet))
    MAX_VALUE = Wei(2**256 - 1)
    tx = contract.approve(address=address, value=MAX_VALUE)
    logger.info('Approve transaction sent, tx hash: %s', tx.hex())

    # Wait for tx receipt
    logger.info('Waiting for tx receipt')
    receipt = execution_client.eth.wait_for_transaction_receipt(
        tx, timeout=EXECUTION_TRANSACTION_TIMEOUT
    )

    # Check receipt status
    if not receipt['status']:
        raise RuntimeError(f'Approve tx failed, tx hash: {tx.hex()}')
    logger.info('Tx confirmed')
