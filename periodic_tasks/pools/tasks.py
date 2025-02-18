import logging

from sw_utils.networks import MAINNET
from web3 import Web3
from web3.types import Wei

from periodic_tasks.common.settings import NETWORK, network_config

from .contracts import get_erc20_contract
from .cow_protocol import CowProtocolWrapper
from .execution import distribute_tokens, get_base_token_balance, wrap_ether
from .settings import (
    MIN_ETH_FOR_GAS_AMOUNT,
    NETWORK_TICKERS,
    TICKER_TO_SETTINGS,
    TOKEN_ADDRESSES,
    WETH_TICKER,
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
        base_to_swap = get_base_token_balance(pool.wallet.address)  # eth or gno amount
        logger.info('')
        # base_to_swap = int(base_to_swap / 2)  # todo

        if base_to_swap < network_config.MIN_POOL_SWAP_AMOUNT:
            logger.info('')
            continue

        # wrap native token
        if NETWORK == MAINNET:
            base_to_swap = Wei(base_to_swap - MIN_ETH_FOR_GAS_AMOUNT)  # gas
            wrap_ether(
                wallet=pool.wallet,
                amount=base_to_swap,
            )

            token_contract = get_erc20_contract(
                address=TOKEN_ADDRESSES[MAINNET][WETH_TICKER],
            )
            base_to_swap = token_contract.get_balance(pool.wallet.address)

        x_token_amount = CowProtocolWrapper().swap(
            wallet=pool.wallet,
            sell_token=pool.swap_from_token,
            buy_token=pool.swap_to_token,
            sell_amount=base_to_swap,
        )
        if not x_token_amount or x_token_amount < 1:
            logger.info('')
            continue
        logger.info('')
        await distribute_tokens(
            token=pool.distribute_token,
            amount=x_token_amount,  # x_token_amount or all balance of wallet
            vault_address=pool.vault_address,
        )
        logger.info('')
