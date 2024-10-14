from dataclasses import dataclass

from eth_typing import ChecksumAddress, HexStr
from sw_utils import convert_to_mgno
from web3 import Web3
from web3.types import Wei

from src.ltv.networks import GNO_NETWORKS
from src.ltv.settings import NETWORK


@dataclass
class HarvestParams:
    rewards_root: bytes
    reward: Wei
    unlocked_mev_reward: Wei
    proof: list[bytes]

    def __str__(self) -> str:
        d = {
            'rewards_root': Web3.to_hex(self.rewards_root),
            'reward': self.reward,
            'unlocked_mev_reward': self.unlocked_mev_reward,
            'proof': [Web3.to_hex(p) for p in self.proof],
        }
        return str(d)


@dataclass
class OwnMevVaultReward:
    vault: ChecksumAddress
    consensus_reward: Wei
    proof: list[HexStr]
    unlocked_mev_reward: Wei
    withdrawals: Wei = Wei(0)

    @property
    def merkle_leaf(self) -> tuple[ChecksumAddress, Wei, Wei]:
        return self.vault, self.consensus_reward, Wei(0)

    @property
    def execution_reward(self) -> Wei:
        return self.unlocked_mev_reward


@dataclass
class SharedMevVaultReward:
    vault: ChecksumAddress
    consensus_reward: Wei
    proof: list[HexStr]
    locked_mev_reward: Wei
    unlocked_mev_reward: Wei
    withdrawals: Wei = Wei(0)

    @property
    def merkle_leaf(self) -> tuple[ChecksumAddress, Wei, Wei]:
        if NETWORK in GNO_NETWORKS:
            sum_rewards = self.consensus_reward
        else:
            sum_rewards = Wei(
                self.consensus_reward + self.locked_mev_reward + self.unlocked_mev_reward
            )
        return self.vault, Wei(sum_rewards), self.unlocked_mev_reward

    @property
    def execution_reward(self) -> Wei:
        return Wei(self.locked_mev_reward + self.unlocked_mev_reward)


@dataclass
class RewardSnapshot:
    vaults: list[OwnMevVaultReward | SharedMevVaultReward]

    @staticmethod
    def from_dict(data: dict) -> 'RewardSnapshot':
        vault_rewards = []
        for vault in data['vaults']:
            if NETWORK in GNO_NETWORKS:
                consensus_reward = convert_to_mgno(vault['consensus_reward'])
                withdrawals = convert_to_mgno(vault['withdrawals'])
            else:
                consensus_reward = vault['consensus_reward']
                withdrawals = Wei(vault['withdrawals'])

            vault_reward: SharedMevVaultReward | OwnMevVaultReward
            if 'locked_mev_reward' in vault:
                vault_reward = SharedMevVaultReward(
                    vault=vault['vault'],
                    consensus_reward=consensus_reward,
                    proof=vault['proof'],
                    locked_mev_reward=vault['locked_mev_reward'],
                    unlocked_mev_reward=vault['unlocked_mev_reward'],
                    withdrawals=withdrawals,
                )
            else:
                vault_reward = OwnMevVaultReward(
                    vault=vault['vault'],
                    consensus_reward=consensus_reward,
                    proof=vault['proof'],
                    unlocked_mev_reward=vault['unlocked_mev_reward'],
                    withdrawals=withdrawals,
                )

            vault_rewards.append(vault_reward)
        return RewardSnapshot(vaults=vault_rewards)
