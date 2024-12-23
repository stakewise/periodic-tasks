from dataclasses import dataclass

from hexbytes import HexBytes
from web3.types import Wei


@dataclass
class HarvestParams:
    rewards_root: HexBytes
    reward: Wei
    unlocked_mev_reward: Wei
    proof: list[HexBytes]
