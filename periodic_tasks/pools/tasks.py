import logging

from periodic_tasks.common.settings import NETWORK

from .cow_protocol import CowProtocolWrapper
from .execution import distribute_tokens, get_eth_balance
from .settings import DDDATA, NETWORK_BASE_TICKER_ADDRESSES, TOKEN_ADDRESSES

logger = logging.getLogger(__name__)


async def handle_pools() -> None:
    """ """
    # block = execution_client.eth.get_block('finalized')
    # logger.debug('Current block: %d', block['number'])
    # block_number = block['number']

    for ddate in DDDATA:
        base_to_swap = get_eth_balance(ddate.wallet_address)  # eth or gno amount
        logger.info('')

        x_token_amount = CowProtocolWrapper().swap(
            sell_token=NETWORK_BASE_TICKER_ADDRESSES[NETWORK],
            buy_token=TOKEN_ADDRESSES[NETWORK][ddate.ticker],
            sell_amount=base_to_swap,
        )
        if not x_token_amount:
            continue

        logger.info('')
        await distribute_tokens(
            token=TOKEN_ADDRESSES[NETWORK][ddate.ticker],
            amount=x_token_amount,
            vault_address=ddate.vault_address,
        )
        logger.info('')
