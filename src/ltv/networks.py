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
            '0xcB85952262C80422E7925593C872fBe49b13C432'
        ),
    ),
    Network.GNOSIS: NetworkConfig(
        VAULT_USER_LTV_TRACKER_CONTRACT_ADDRESS=ZERO_CHECKSUM_ADDRESS,
    ),
    Network.CHIADO: NetworkConfig(
        VAULT_USER_LTV_TRACKER_CONTRACT_ADDRESS=ZERO_CHECKSUM_ADDRESS,
    ),
}
