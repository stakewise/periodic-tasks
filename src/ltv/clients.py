import logging

import gql
from eth_account import Account
from gql.transport.requests import RequestsHTTPTransport
from sw_utils import IpfsFetchClient
from web3 import Web3
from web3.middleware import construct_sign_and_send_raw_middleware

from .settings import (
    EXECUTION_ENDPOINT,
    GRAPH_API_TIMEOUT,
    GRAPH_API_URL,
    HOT_WALLET_PRIVATE_KEY,
    IPFS_FETCH_CLIENT_TIMEOUT,
    IPFS_FETCH_ENDPOINTS,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

hot_wallet_account = Account().from_key(HOT_WALLET_PRIVATE_KEY)
execution_client = Web3(Web3.HTTPProvider(EXECUTION_ENDPOINT))
execution_client.middleware_onion.add(construct_sign_and_send_raw_middleware(hot_wallet_account))
logger.info('hot wallet address: %s', hot_wallet_account.address)


def get_graph_client() -> gql.Client:
    if GRAPH_API_URL is None:
        raise ValueError('GRAPH_API_URL must be set')

    if GRAPH_API_TIMEOUT is None:
        raise ValueError('GRAPH_API_TIMEOUT must be set')

    transport = RequestsHTTPTransport(
        url=GRAPH_API_URL,
        timeout=GRAPH_API_TIMEOUT,
    )
    return gql.Client(transport=transport)


graph_client = get_graph_client()

ipfs_fetch_client = IpfsFetchClient(
    ipfs_endpoints=IPFS_FETCH_ENDPOINTS,
    timeout=IPFS_FETCH_CLIENT_TIMEOUT,
)
