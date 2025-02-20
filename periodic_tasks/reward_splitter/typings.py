from dataclasses import dataclass

from eth_typing import ChecksumAddress


@dataclass
class RewardSplitterShareHolder:
    address: ChecksumAddress


@dataclass
class RewardSplitter:
    address: ChecksumAddress
    vault: ChecksumAddress
    shareholders: list[RewardSplitterShareHolder]
