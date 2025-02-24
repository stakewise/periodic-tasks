from dataclasses import asdict, dataclass

from ens.constants import EMPTY_ADDR_HEX
from eth_typing import ChecksumAddress
from sw_utils.networks import CHIADO, GNOSIS, HOLESKY, MAINNET
from sw_utils.networks import NETWORKS as BASE_NETWORKS
from sw_utils.networks import BaseNetworkConfig
from web3 import Web3
from web3.types import Wei

ZERO_CHECKSUM_ADDRESS = Web3.to_checksum_address(EMPTY_ADDR_HEX)  # noqa

SEPOLIA = 'sepolia'


@dataclass
class PriceNetworkConfig:
    # TARGET_CHAIN is not what eth_chainId returns.
    # It is internal id used in PriceFeedSender contract.
    TARGET_CHAIN: int
    # PriceFeedReceiver contract address on target network
    TARGET_ADDRESS: ChecksumAddress
    # PriceFeed contract address on target network
    TARGET_PRICE_FEED_CONTRACT_ADDRESS: ChecksumAddress
    # PriceFeedSender contract address on sender network
    PRICE_FEED_SENDER_CONTRACT_ADDRESS: ChecksumAddress


PRICE_NETWORKS: dict[str, PriceNetworkConfig | None] = {
    MAINNET: PriceNetworkConfig(
        # TARGET_CHAIN is not what eth_chainId returns.
        # It is internal id used in PriceFeedSender contract.
        TARGET_CHAIN=23,
        # PriceFeedReceiver contract address on Arbitrum
        TARGET_ADDRESS=Web3.to_checksum_address('0xbd335c16c94be8c4dd073ae376ddf78bec1858df'),
        # PriceFeed contract address on Arbitrum
        TARGET_PRICE_FEED_CONTRACT_ADDRESS=Web3.to_checksum_address(
            '0xba74737a078c05500dd98c970909e4a3b90c35c6'
        ),
        # PriceFeedSender contract address on Mainnet
        PRICE_FEED_SENDER_CONTRACT_ADDRESS=Web3.to_checksum_address(
            '0xf7d4e7273e5015c96728a6b02f31c505ee184603'
        ),
    ),
    HOLESKY: None,
    GNOSIS: None,
    CHIADO: None,
    SEPOLIA: PriceNetworkConfig(
        # TARGET_CHAIN is not what eth_chainId returns.
        # It is internal id used in PriceFeedSender contract.
        TARGET_CHAIN=10003,
        # PriceFeedReceiver contract address on Arbitrum Sepolia
        TARGET_ADDRESS=Web3.to_checksum_address('0x744836a91f5151c6ef730eb7e07c232997debaaa'),
        # PriceFeed contract address on Arbitrum Sepolia
        TARGET_PRICE_FEED_CONTRACT_ADDRESS=Web3.to_checksum_address(
            '0x4026affabd9032bcc87fa05c02f088905f3dc09b'
        ),
        # PriceFeedSender contract address on Sepolia
        PRICE_FEED_SENDER_CONTRACT_ADDRESS=Web3.to_checksum_address(
            '0xe572a8631a49ec4c334812bb692beecf934ac4e9'
        ),
    ),
}


@dataclass
class NetworkConfig(BaseNetworkConfig):
    VAULT_USER_LTV_TRACKER_CONTRACT_ADDRESS: ChecksumAddress
    LEVERAGE_STRATEGY_CONTRACT_ADDRESS: ChecksumAddress
    STRATEGY_REGISTRY_CONTRACT_ADDRESS: ChecksumAddress
    OSTOKEN_ESCROW_CONTRACT_ADDRESS: ChecksumAddress
    TOKEN_DISTRIBUTOR_CONTRACT_ADDRESS: ChecksumAddress
    COWSWAP_API_URL: str | None
    COWSWAP_VAULT_RELAYER_CONTRACT_ADDRESS: ChecksumAddress
    COWSWAP_VERIFYING_CONTRACT_ADDRESS: ChecksumAddress
    MIN_POOL_SWAP_AMOUNT: Wei


NETWORKS: dict[str, NetworkConfig] = {
    MAINNET: NetworkConfig(
        **asdict(BASE_NETWORKS[MAINNET]),
        VAULT_USER_LTV_TRACKER_CONTRACT_ADDRESS=Web3.to_checksum_address(
            '0xe0Ae8B04922d6e3fA06c2496A94EF2875EFcC7BB'
        ),
        LEVERAGE_STRATEGY_CONTRACT_ADDRESS=Web3.to_checksum_address(
            '0x48cD14FDB8e72A03C8D952af081DBB127D6281fc'
        ),
        STRATEGY_REGISTRY_CONTRACT_ADDRESS=Web3.to_checksum_address(
            '0x90b82E4b3aa385B4A02B7EBc1892a4BeD6B5c465'
        ),
        OSTOKEN_ESCROW_CONTRACT_ADDRESS=Web3.to_checksum_address(
            '0x09e84205DF7c68907e619D07aFD90143c5763605'
        ),
        TOKEN_DISTRIBUTOR_CONTRACT_ADDRESS=ZERO_CHECKSUM_ADDRESS,
        COWSWAP_API_URL='https://api.cow.fi/mainnet',
        COWSWAP_VAULT_RELAYER_CONTRACT_ADDRESS=Web3.to_checksum_address(
            '0xC92E8bdf79f0507f65a392b0ab4667716BFE0110'
        ),
        COWSWAP_VERIFYING_CONTRACT_ADDRESS=Web3.to_checksum_address(
            '0x9008D19f58AAbD9eD0D60971565AA8510560ab41'
        ),
        MIN_POOL_SWAP_AMOUNT=Wei(Web3.to_wei(0.01, 'ether')),
    ),
    HOLESKY: NetworkConfig(
        **asdict(BASE_NETWORKS[HOLESKY]),
        VAULT_USER_LTV_TRACKER_CONTRACT_ADDRESS=Web3.to_checksum_address(
            '0x8f48130b9b96B58035b4A9389eCDaBC00d59d0c8'
        ),
        LEVERAGE_STRATEGY_CONTRACT_ADDRESS=Web3.to_checksum_address(
            '0xdB38cfc6e98a34Cdc60c568f607417E646C75B34'
        ),
        STRATEGY_REGISTRY_CONTRACT_ADDRESS=Web3.to_checksum_address(
            '0xFc8E3E7c919b4392D9F5B27015688e49c80015f0'
        ),
        OSTOKEN_ESCROW_CONTRACT_ADDRESS=Web3.to_checksum_address(
            '0x807305c086A99cbDBff07cB4256cE556d9d6F0af'
        ),
        TOKEN_DISTRIBUTOR_CONTRACT_ADDRESS=ZERO_CHECKSUM_ADDRESS,
        COWSWAP_API_URL=None,
        COWSWAP_VAULT_RELAYER_CONTRACT_ADDRESS=ZERO_CHECKSUM_ADDRESS,
        COWSWAP_VERIFYING_CONTRACT_ADDRESS=ZERO_CHECKSUM_ADDRESS,
        MIN_POOL_SWAP_AMOUNT=Wei(0),
    ),
    GNOSIS: NetworkConfig(
        **asdict(BASE_NETWORKS[GNOSIS]),
        VAULT_USER_LTV_TRACKER_CONTRACT_ADDRESS=Web3.to_checksum_address(
            '0xdEa72c54f63470349CE2dC12f8232FE00241abE6'
        ),
        LEVERAGE_STRATEGY_CONTRACT_ADDRESS=ZERO_CHECKSUM_ADDRESS,
        STRATEGY_REGISTRY_CONTRACT_ADDRESS=ZERO_CHECKSUM_ADDRESS,
        OSTOKEN_ESCROW_CONTRACT_ADDRESS=ZERO_CHECKSUM_ADDRESS,
        TOKEN_DISTRIBUTOR_CONTRACT_ADDRESS=ZERO_CHECKSUM_ADDRESS,
        COWSWAP_API_URL='https://api.cow.fi/xdai',
        COWSWAP_VAULT_RELAYER_CONTRACT_ADDRESS=Web3.to_checksum_address(
            '0xC92E8bdf79f0507f65a392b0ab4667716BFE0110'
        ),
        COWSWAP_VERIFYING_CONTRACT_ADDRESS=Web3.to_checksum_address(
            '0x9008D19f58AAbD9eD0D60971565AA8510560ab41'
        ),
        MIN_POOL_SWAP_AMOUNT=Wei(Web3.to_wei(0.1, 'ether')),
    ),
    CHIADO: NetworkConfig(
        **asdict(BASE_NETWORKS[CHIADO]),
        VAULT_USER_LTV_TRACKER_CONTRACT_ADDRESS=Web3.to_checksum_address(
            '0xe0Ae8B04922d6e3fA06c2496A94EF2875EFcC7BB'
        ),
        LEVERAGE_STRATEGY_CONTRACT_ADDRESS=ZERO_CHECKSUM_ADDRESS,
        STRATEGY_REGISTRY_CONTRACT_ADDRESS=ZERO_CHECKSUM_ADDRESS,
        OSTOKEN_ESCROW_CONTRACT_ADDRESS=ZERO_CHECKSUM_ADDRESS,
        TOKEN_DISTRIBUTOR_CONTRACT_ADDRESS=ZERO_CHECKSUM_ADDRESS,
        COWSWAP_API_URL=None,
        COWSWAP_VAULT_RELAYER_CONTRACT_ADDRESS=ZERO_CHECKSUM_ADDRESS,
        COWSWAP_VERIFYING_CONTRACT_ADDRESS=ZERO_CHECKSUM_ADDRESS,
        MIN_POOL_SWAP_AMOUNT=Wei(0),
    ),
}
