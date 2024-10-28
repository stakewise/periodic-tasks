from dataclasses import dataclass
from enum import Enum

from eth_typing import ChecksumAddress, HexAddress, HexStr
from web3 import Web3

EMPTY_ADDR_HEX = HexAddress(HexStr('0x' + '00' * 20))
ZERO_CHECKSUM_ADDRESS = Web3.to_checksum_address(EMPTY_ADDR_HEX)  # noqa


class Network(Enum):
    MAINNET = 'mainnet'
    HOLESKY = 'holesky'
    GNOSIS = 'gnosis'
    CHIADO = 'chiado'


@dataclass
class NetworkConfig:
    VAULT_USER_LTV_TRACKER_CONTRACT_ADDRESS: ChecksumAddress


NETWORKS: dict[Network, NetworkConfig] = {
    Network.MAINNET: NetworkConfig(
        VAULT_USER_LTV_TRACKER_CONTRACT_ADDRESS=Web3.to_checksum_address(
            '0xe0Ae8B04922d6e3fA06c2496A94EF2875EFcC7BB'
        ),
    ),
    Network.HOLESKY: NetworkConfig(
        VAULT_USER_LTV_TRACKER_CONTRACT_ADDRESS=Web3.to_checksum_address(
            '0x8f48130b9b96B58035b4A9389eCDaBC00d59d0c8'
        ),
    ),
    Network.GNOSIS: NetworkConfig(
        VAULT_USER_LTV_TRACKER_CONTRACT_ADDRESS=Web3.to_checksum_address(
            '0xdEa72c54f63470349CE2dC12f8232FE00241abE6'
        ),
    ),
    Network.CHIADO: NetworkConfig(
        VAULT_USER_LTV_TRACKER_CONTRACT_ADDRESS=Web3.to_checksum_address(
            '0xe0Ae8B04922d6e3fA06c2496A94EF2875EFcC7BB'
        ),
    ),
}
