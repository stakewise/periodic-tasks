import asyncio
import logging
import time
from datetime import datetime, timezone

import requests
from eth_account.messages import encode_typed_data
from eth_account.signers.local import LocalAccount
from sw_utils.common import urljoin
from web3 import Web3
from web3.types import ChecksumAddress, Wei

from periodic_tasks.common.settings import network_config

from .contracts import get_erc20_contract
from .execution import approve_spending
from .settings import (
    COWSWAP_ORDER_PROCESSING_SLEEP,
    COWSWAP_ORDER_PROCESSING_TIMEOUT,
    COWSWAP_REQUEST_TIMEOUT,
)

logger = logging.getLogger(__name__)

EMPTY_APP_DATA = '0x0000000000000000000000000000000000000000000000000000000000000000'


class CowProtocolWrapper:
    async def swap(
        self,
        wallet: LocalAccount,
        sell_token: ChecksumAddress,
        buy_token: ChecksumAddress,
        sell_amount: Wei,
    ) -> Wei | None:
        await self._approve_sell_token(
            wallet=wallet,
            sell_token=sell_token,
            sell_amount=sell_amount,
        )

        quote = self._quote(
            wallet=wallet,
            sell_token=sell_token,
            buy_token=buy_token,
            sell_amount=sell_amount,
        )

        if not quote:
            return None
        order_uid = self._submit_order(
            wallet=wallet,
            quote=quote,
        )
        logger.info('Created CowSwap order %s', order_uid)
        if not order_uid:
            return None

        await asyncio.sleep(3)  # wait for order processing
        start_time = time.time()
        while True:
            order_data = self._check_order(order_uid)
            if order_data:
                if order_data['status'] == 'fulfilled':
                    return Wei(int(order_data['executedBuyAmount']))
                if order_data['status'] in ['cancelled', 'expired']:
                    logging.error('Failed to fetch cowswap order %s', order_uid)
                    return None
                if order_data['validTo'] < int(datetime.now(timezone.utc).timestamp()):
                    logging.error(
                        'Failed to fill cowswap order %s within the processing time', order_uid
                    )
                    return None
            elif time.time() > start_time + COWSWAP_ORDER_PROCESSING_TIMEOUT:
                logging.error('Failed to fetch cowswap order %s', order_uid)
                return None
            await asyncio.sleep(COWSWAP_ORDER_PROCESSING_SLEEP)

    async def _approve_sell_token(
        self,
        wallet: LocalAccount,
        sell_token: ChecksumAddress,
        sell_amount: Wei,
    ) -> None:
        sell_token_contract = get_erc20_contract(sell_token)
        allowance = await sell_token_contract.get_allowance(
            wallet.address, network_config.COWSWAP_VAULT_RELAYER_CONTRACT_ADDRESS
        )

        if allowance < sell_amount:
            await approve_spending(
                token=sell_token,
                address=network_config.COWSWAP_VAULT_RELAYER_CONTRACT_ADDRESS,
                wallet=wallet,
            )

    def _quote(
        self,
        wallet: LocalAccount,
        sell_token: ChecksumAddress,
        buy_token: ChecksumAddress,
        sell_amount: Wei,
    ) -> dict | None:
        payload = {
            'sellToken': sell_token,
            'buyToken': buy_token,
            'receiver': wallet.address,
            'appData': EMPTY_APP_DATA,
            'sellTokenBalance': 'erc20',
            'buyTokenBalance': 'erc20',
            'from': wallet.address,
            'priceQuality': 'verified',
            'signingScheme': 'eip712',
            'onchainOrder': False,
            'kind': 'sell',
            'sellAmountBeforeFee': str(sell_amount),
        }
        response = requests.post(
            urljoin(network_config.COWSWAP_API_URL, '/api/v1/quote'),
            json=payload,
            timeout=COWSWAP_REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        if response.status_code == 200:
            data = response.json()

            if not data.get('verified'):
                logger.error('Failed to verify cowswap order')
                return None
            return data
        logger.error('Failed to quote cowswap order: %s', response.text)
        return None

    def _submit_order(
        self,
        wallet: LocalAccount,
        quote: dict,
    ) -> str | None:
        quote_data = quote['quote']
        order_payload = {
            'sellToken': quote_data['sellToken'],
            'buyToken': quote_data['buyToken'],
            'sellAmount': quote_data['sellAmount'],
            'buyAmount': quote_data['buyAmount'],
            'sellTokenBalance': quote_data['sellTokenBalance'],
            'buyTokenBalance': quote_data['sellTokenBalance'],
            'validTo': quote_data['validTo'],
            'feeAmount': '0',
            'kind': quote_data['kind'],
            'partiallyFillable': quote_data['partiallyFillable'],
            'receiver': wallet.address,
            'signingScheme': quote_data['signingScheme'],
            'from': wallet.address,
            'quoteId': quote['id'],
            'appData': EMPTY_APP_DATA,
        }
        signing_message = CowProtocolWrapper._get_signing_message(order_payload)
        encoded_message = encode_typed_data(full_message=signing_message)
        signature = wallet.sign_message(encoded_message).signature
        signature = Web3.to_hex(signature)
        order_payload['signature'] = signature
        response = requests.post(
            urljoin(network_config.COWSWAP_API_URL, '/api/v1/orders'),
            json=order_payload,
            timeout=COWSWAP_REQUEST_TIMEOUT,
        )
        if response.status_code == 201:
            return response.json()

        logger.error('Failed to submit cowswap order: %s', response.text)
        return None

    def _check_order(self, order_uid: str) -> dict | None:
        response = requests.get(
            urljoin(network_config.COWSWAP_API_URL, '/api/v1/orders', order_uid),
            timeout=COWSWAP_REQUEST_TIMEOUT,
        )
        if response.status_code == 403:  # rate limit
            return None
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _get_signing_message(order_payload: dict) -> dict:
        data = {
            'primaryType': 'Order',
            'types': {
                'EIP712Domain': [
                    {'name': 'name', 'type': 'string'},
                    {'name': 'version', 'type': 'string'},
                    {'name': 'chainId', 'type': 'uint256'},
                    {'name': 'verifyingContract', 'type': 'address'},
                ],
                'Order': [
                    {'name': 'sellToken', 'type': 'address'},
                    {'name': 'buyToken', 'type': 'address'},
                    {'name': 'receiver', 'type': 'address'},
                    {'name': 'sellAmount', 'type': 'uint256'},
                    {'name': 'buyAmount', 'type': 'uint256'},
                    {'name': 'validTo', 'type': 'uint32'},
                    {'name': 'appData', 'type': 'bytes32'},
                    {'name': 'feeAmount', 'type': 'uint256'},
                    {'name': 'kind', 'type': 'string'},
                    {'name': 'partiallyFillable', 'type': 'bool'},
                    {'name': 'sellTokenBalance', 'type': 'string'},
                    {'name': 'buyTokenBalance', 'type': 'string'},
                ],
            },
            'domain': {
                'name': 'Gnosis Protocol',
                'version': 'v2',
                'chainId': network_config.CHAIN_ID,
                'verifyingContract': network_config.COWSWAP_VERIFYING_CONTRACT_ADDRESS,
            },
            'message': order_payload,
        }
        return data
