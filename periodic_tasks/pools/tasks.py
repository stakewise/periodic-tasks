import logging

from eth_account.signers.local import LocalAccount
from sw_utils.networks import MAINNET
from web3 import Web3
from web3.types import Wei

from periodic_tasks.common.settings import NETWORK, network_config

from .contracts import get_erc20_contract
from .cow_protocol import CowProtocolWrapper
from .execution import (
    approve_spending,
    convert_to_susds,
    distribute_tokens,
    get_base_token_balance,
    wrap_ether,
)
from .settings import (
    MIN_ETH_FOR_GAS_AMOUNT,
    NETWORK_BASE_TICKERS,
    NETWORK_TICKERS,
    SUSDS_TICKER,
    TICKER_TO_SETTINGS,
    TOKEN_ADDRESSES,
    USDS_TICKER,
    WETH_TICKER,
)
from .typings import PoolSettings

logger = logging.getLogger(__name__)


async def handle_pools() -> None:
    """
    Handle diversify infinity pools
    - Swap vault rewards from the connected wallet via cowswap to BTC/SOL/sUSDS ...
    - Distribute the swapped tokens using the MerkleDistributor contract.
    Corner cases:
    - Cowswap only supports ERC20 token, so ETH must be converted to WETH before swapping.
    - Swap to USDS instead of sUSDS, then convert USDS to sUSDS via contract
    """
    pool_settings = _build_pool_settings()
    for pool in pool_settings:
        base_to_swap = await get_base_token_balance(pool.wallet.address)  # eth or gno amount
        logger.info(
            'Processing %s %s for vault %s. Wallet address: %s ...',
            Web3.from_wei(base_to_swap, 'ether'),
            NETWORK_BASE_TICKERS[NETWORK],
            pool.vault_address,
            pool.wallet.address,
        )

        if base_to_swap < network_config.MIN_POOL_SWAP_AMOUNT:
            logger.info('Distributed amount too small, skipping vault %s...', pool.vault_address)
            continue

        # wrap native eth for mainnet
        if NETWORK == MAINNET:
            base_to_swap = await _convert_to_weth(wallet=pool.wallet, amount=base_to_swap)

        swapped_amount = await CowProtocolWrapper().swap(
            wallet=pool.wallet,
            sell_token=pool.swap_from_token,
            buy_token=pool.swap_to_token,
            sell_amount=base_to_swap,
        )
        if swapped_amount:
            logger.info(
                'Swapped %s %s via CowSwap for vault %s...',
                Web3.from_wei(swapped_amount, 'ether'),
                pool.ticker,
                pool.vault_address,
            )

        else:
            logger.info('Can\'t swap tokens via CowSwap, skipping vault %s...', pool.vault_address)
            continue

        if pool.ticker == USDS_TICKER:
            await _convert_to_susds(pool.wallet)
            logger.info(
                'Successfully converted %s to %s for vault %s...',
                USDS_TICKER,
                SUSDS_TICKER,
                pool.vault_address,
            )

        distributed_token_contract = get_erc20_contract(
            address=pool.distributed_token,
        )
        distributed_token_amount = await distributed_token_contract.get_balance(pool.wallet.address)
        logger.info(
            'Distributing %s %s for vault %s...',
            Web3.from_wei(distributed_token_amount, 'ether'),
            pool.ticker,
            pool.vault_address,
        )

        await distribute_tokens(
            token=pool.distributed_token,
            amount=distributed_token_amount,
            vault_address=pool.vault_address,
        )
        logger.info('Vault %s was processed successfully')


def _build_pool_settings() -> list[PoolSettings]:
    pool_settings: list[PoolSettings] = []
    for ticker in NETWORK_TICKERS[NETWORK]:
        wallet = TICKER_TO_SETTINGS[ticker][0]
        vault_address = TICKER_TO_SETTINGS[ticker][1]
        if not wallet:
            continue
        if not vault_address:
            logger.warning('Missed vault environment variable for ticker %s', ticker)
            continue
        vault_address = Web3.to_checksum_address(vault_address)
        pool_settings.append(
            PoolSettings(
                ticker=ticker,
                wallet=wallet,
                vault_address=vault_address,
            )
        )

    return pool_settings


async def _convert_to_weth(wallet: LocalAccount, amount: Wei) -> Wei:
    """Convert ETH to WETH"""
    converted_amount = Wei(amount - MIN_ETH_FOR_GAS_AMOUNT)
    await wrap_ether(
        wallet=wallet,
        amount=converted_amount,
    )

    token_contract = get_erc20_contract(
        address=TOKEN_ADDRESSES[MAINNET][WETH_TICKER],
    )
    return await token_contract.get_balance(wallet.address)


async def _convert_to_susds(wallet: LocalAccount) -> None:
    """Convert USDS to sUSDS via contract deposit"""
    usds_token_contract = get_erc20_contract(
        address=TOKEN_ADDRESSES[MAINNET][USDS_TICKER],
    )
    usds_amount = await usds_token_contract.get_balance(wallet.address)

    allowance = await usds_token_contract.get_allowance(
        owner=wallet.address, spender=TOKEN_ADDRESSES[MAINNET][SUSDS_TICKER]
    )
    if allowance < usds_amount:
        await approve_spending(
            token=TOKEN_ADDRESSES[MAINNET][USDS_TICKER],
            address=TOKEN_ADDRESSES[MAINNET][SUSDS_TICKER],
            wallet=wallet,
        )

    await convert_to_susds(amount=usds_amount, wallet=wallet)
