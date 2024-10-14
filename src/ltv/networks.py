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


ETH_NETWORKS = [Network.MAINNET, Network.HOLESKY]
GNO_NETWORKS = [Network.GNOSIS, Network.CHIADO]


@dataclass
class NetworkConfig:
    SECONDS_PER_BLOCK: int
    VAULT_USER_LTV_TRACKER_CONTRACT_ADDRESS: ChecksumAddress
    KEEPER_CONTRACT_ADDRESS: ChecksumAddress


NETWORKS: dict[Network, NetworkConfig] = {
    Network.MAINNET: NetworkConfig(
        SECONDS_PER_BLOCK=12,
        VAULT_USER_LTV_TRACKER_CONTRACT_ADDRESS=ZERO_CHECKSUM_ADDRESS,
        KEEPER_CONTRACT_ADDRESS=ZERO_CHECKSUM_ADDRESS,
    ),
    Network.HOLESKY: NetworkConfig(
        SECONDS_PER_BLOCK=12,
        VAULT_USER_LTV_TRACKER_CONTRACT_ADDRESS=Web3.to_checksum_address(
            '0xB0A6f7eFfB7e45874ec307C1D5BC18E465c83D39'
        ),
        KEEPER_CONTRACT_ADDRESS=Web3.to_checksum_address(
            '0xB580799Bf7d62721D1a523f0FDF2f5Ed7BA4e259'
        ),
    ),
    Network.GNOSIS: NetworkConfig(
        SECONDS_PER_BLOCK=5,
        VAULT_USER_LTV_TRACKER_CONTRACT_ADDRESS=ZERO_CHECKSUM_ADDRESS,
        KEEPER_CONTRACT_ADDRESS=ZERO_CHECKSUM_ADDRESS,
    ),
    Network.CHIADO: NetworkConfig(
        SECONDS_PER_BLOCK=5,
        VAULT_USER_LTV_TRACKER_CONTRACT_ADDRESS=ZERO_CHECKSUM_ADDRESS,
        KEEPER_CONTRACT_ADDRESS=ZERO_CHECKSUM_ADDRESS,
    ),
}
