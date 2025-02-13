import json
import logging
import time

import requests
from eth_account.signers.local import LocalAccount
from web3 import Web3
from web3.types import ChecksumAddress, Wei

from periodic_tasks.common.settings import network_config

from .settings import COWSWAP_ORDER_PROCESSING_TIMEOUT, COWSWAP_REQUEST_TIMEOUT

logger = logging.getLogger(__name__)


class CowProtocolWrapper:
    def swap(
        self,
        wallet: LocalAccount,
        sell_token: ChecksumAddress,
        buy_token: ChecksumAddress,
        sell_amount: Wei,
    ) -> Wei | None:
        order_uid = self._submit_order(
            wallet=wallet,
            sell_token=sell_token,
            buy_token=buy_token,
            sell_amount=sell_amount,
        )
        if not order_uid:
            return None

        start_time = time.time()
        while True:
            converted_amount = self._check_order(order_uid)
            if converted_amount:
                return converted_amount

            if time.time() > start_time + COWSWAP_ORDER_PROCESSING_TIMEOUT:
                logging.error('Failed to process cowswap order %s', order_uid)
                return None
            time.sleep(0.5)

    def _submit_order(
        self,
        wallet: LocalAccount,
        sell_token: ChecksumAddress,
        buy_token: ChecksumAddress,
        sell_amount: Wei,
    ) -> str | None:
        buy_amount = 0  # todo
        order_payload = {
            'sellToken': sell_token,
            'buyToken': buy_token,
            'sellAmount': str(sell_amount),
            'buyAmount': str(buy_amount),
            'validTo': 0,  # Use 0 for immediate execution
            'appData': '0x0000000000000000000000000000000000000000000000000000000000000000',
            'feeAmount': '0',
            'kind': 'sell',  # "sell" or "buy"
            'partiallyFillable': False,
            'receiver': wallet.address,
            'signature': '',
            'signingScheme': 'eip712',
            'from': wallet.address,
        }

        order_payload['signature'] = wallet.sign_message(
            Web3.keccak(text=json.dumps(order_payload))
        ).signature.hex()

        response = requests.post(
            f'{network_config.COWSWAP_API_URL}/orders',
            json=order_payload,
            timeout=COWSWAP_REQUEST_TIMEOUT,
        )
        if response.status_code == 201:
            logger.info('Order submitted successfully!')
            return response.json()

        logger.error('Failed to submit order.: %s', response.text)
        return None

    def _check_order(self, order_uid: str) -> Wei | None:
        response = requests.get(
            f'{network_config.COWSWAP_API_URL}/orders/{order_uid}/check',
            timeout=COWSWAP_REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        if data['status'] == 'closed?':
            return Wei(data['value']['executedAmounts']['buy'])  # todo Wei?
        return None
