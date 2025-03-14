from dataclasses import dataclass

from eth_typing import ChecksumAddress
from hexbytes import HexBytes
from web3.types import Wei


@dataclass
class HarvestParams:
    rewards_root: HexBytes
    reward: Wei
    unlocked_mev_reward: Wei
    proof: list[HexBytes]


@dataclass
class Vault:
    address: ChecksumAddress
    can_harvest: bool
    rewards_root: HexBytes
    proof_reward: Wei
    proof_unlocked_mev_reward: Wei
    proof: list[HexBytes]

    @property
    def harvest_params(self) -> HarvestParams:
        return HarvestParams(
            rewards_root=self.rewards_root,
            reward=self.proof_reward,
            unlocked_mev_reward=self.proof_unlocked_mev_reward,
            proof=self.proof,
        )
