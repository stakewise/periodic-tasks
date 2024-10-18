from dataclasses import dataclass
from enum import Enum

from eth_typing import ChecksumAddress, HexAddress, HexStr
from web3 import Web3

EMPTY_ADDR_HEX = HexAddress(HexStr('0x' + '00' * 20))
ZERO_CHECKSUM_ADDRESS = Web3.to_checksum_address(EMPTY_ADDR_HEX)


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
        VAULT_USER_LTV_TRACKER_CONTRACT_ADDRESS=ZERO_CHECKSUM_ADDRESS,
    ),
    Network.HOLESKY: NetworkConfig(
        VAULT_USER_LTV_TRACKER_CONTRACT_ADDRESS=Web3.to_checksum_address(
            '0xB0A6f7eFfB7e45874ec307C1D5BC18E465c83D39'
        ),
    ),
    Network.GNOSIS: NetworkConfig(
        VAULT_USER_LTV_TRACKER_CONTRACT_ADDRESS=ZERO_CHECKSUM_ADDRESS,
    ),
    Network.CHIADO: NetworkConfig(
        VAULT_USER_LTV_TRACKER_CONTRACT_ADDRESS=ZERO_CHECKSUM_ADDRESS,
    ),
}
