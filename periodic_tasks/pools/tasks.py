import logging

from web3 import Web3

from periodic_tasks.common.settings import NETWORK

from .cow_protocol import CowProtocolWrapper
from .execution import distribute_tokens, get_eth_balance
from .settings import (
    NETWORK_BASE_TICKER_ADDRESSES,
    NETWORK_TICKERS,
    TICKER_TO_SETTINGS,
    TOKEN_ADDRESSES,
)
from .typings import PoolSettings

logger = logging.getLogger(__name__)


async def handle_pools() -> None:
    """ """
    pool_settings: list[PoolSettings] = []
    for ticker in NETWORK_TICKERS[NETWORK]:
        wallet = TICKER_TO_SETTINGS[ticker][0]
        vault_address = TICKER_TO_SETTINGS[ticker][1]
        if not wallet:
            continue
        if not vault_address:
            logger.warning('')
            continue
        vault_address = Web3.to_checksum_address(vault_address)
        if all(TICKER_TO_SETTINGS.get(ticker, [])):
            pool_settings.append(
                PoolSettings(
                    ticker=ticker,
                    wallet=wallet,
                    vault_address=vault_address,
                )
            )

    for pool in pool_settings:
        base_to_swap = get_eth_balance(pool.wallet_address)  # eth or gno amount
        logger.info('')

        x_token_amount = CowProtocolWrapper().swap(
            wallet=pool.wallet,
            sell_token=NETWORK_BASE_TICKER_ADDRESSES[NETWORK],
            buy_token=TOKEN_ADDRESSES[NETWORK][pool.ticker],
            sell_amount=base_to_swap,
        )
        if not x_token_amount or x_token_amount < 1:
            logger.info('')
            continue

        logger.info('')
        await distribute_tokens(
            token=TOKEN_ADDRESSES[NETWORK][pool.ticker],
            amount=x_token_amount,  # x_token_amount or all balance of wallet
            vault_address=pool.vault_address,
        )
        logger.info('')
