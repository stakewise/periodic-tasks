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
    SEPOLIA = 'sepolia'


@dataclass
class PriceNetworkConfig:
    # TARGET_CHAIN is not what eth_chainId returns. It is internal id used in PriceFeedSender contract.
    TARGET_CHAIN: int
    # PriceFeedReceiver contract address on target network
    TARGET_ADDRESS: ChecksumAddress
    # PriceFeed contract address on target network
    TARGET_PRICE_FEED_CONTRACT_ADDRESS: ChecksumAddress
    # PriceFeedSender contract address on sender network
    PRICE_FEED_SENDER_CONTRACT_ADDRESS: ChecksumAddress


@dataclass
class NetworkConfig:
    VAULT_USER_LTV_TRACKER_CONTRACT_ADDRESS: ChecksumAddress
    PRICE_NETWORK_CONFIG: PriceNetworkConfig | None = None


NETWORKS: dict[Network, NetworkConfig] = {
    Network.MAINNET: NetworkConfig(
        VAULT_USER_LTV_TRACKER_CONTRACT_ADDRESS=Web3.to_checksum_address(
            '0xe0Ae8B04922d6e3fA06c2496A94EF2875EFcC7BB'
        ),
        PRICE_NETWORK_CONFIG=(
            PriceNetworkConfig(
                # TARGET_CHAIN is not what eth_chainId returns.
                # It is internal id used in PriceFeedSender contract.
                TARGET_CHAIN=23,
                # PriceFeedReceiver contract address on Arbitrum
                TARGET_ADDRESS=Web3.to_checksum_address(
                    '0xbd335c16c94be8c4dd073ae376ddf78bec1858df'
                ),
                # PriceFeed contract address on Arbitrum
                TARGET_PRICE_FEED_CONTRACT_ADDRESS=Web3.to_checksum_address(
                    '0xba74737a078c05500dd98c970909e4a3b90c35c6'
                ),
                # PriceFeedSender contract address on Mainnet
                PRICE_FEED_SENDER_CONTRACT_ADDRESS=Web3.to_checksum_address(
                    '0xf7d4e7273e5015c96728a6b02f31c505ee184603'
                ),
            )
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
    Network.SEPOLIA: NetworkConfig(
        VAULT_USER_LTV_TRACKER_CONTRACT_ADDRESS=ZERO_CHECKSUM_ADDRESS,
        PRICE_NETWORK_CONFIG=(
            PriceNetworkConfig(
                # TARGET_CHAIN is not what eth_chainId returns.
                # It is internal id used in PriceFeedSender contract.
                TARGET_CHAIN=10003,
                # PriceFeedReceiver contract address on Arbitrum Sepolia
                TARGET_ADDRESS=Web3.to_checksum_address(
                    '0x744836a91f5151c6ef730eb7e07c232997debaaa'
                ),
                # PriceFeed contract address on Arbitrum Sepolia
                TARGET_PRICE_FEED_CONTRACT_ADDRESS=Web3.to_checksum_address(
                    '0x4026affabd9032bcc87fa05c02f088905f3dc09b'
                ),
                # PriceFeedSender contract address on Sepolia
                PRICE_FEED_SENDER_CONTRACT_ADDRESS=Web3.to_checksum_address(
                    '0xe572a8631a49ec4c334812bb692beecf934ac4e9'
                ),
            )
        ),
    ),
}
