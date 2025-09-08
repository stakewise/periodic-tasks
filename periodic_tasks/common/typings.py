from dataclasses import dataclass

from eth_typing import ChecksumAddress
from hexbytes import HexBytes
from web3 import Web3
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

    # harvest params
    can_harvest: bool
    rewards_root: HexBytes
    proof_reward: Wei
    proof_unlocked_mev_reward: Wei
    proof: list[HexBytes]

    # meta vaults
    is_meta_vault: bool
    sub_vaults: list[ChecksumAddress]

    @property
    def harvest_params(self) -> HarvestParams:
        return HarvestParams(
            rewards_root=self.rewards_root,
            reward=self.proof_reward,
            unlocked_mev_reward=self.proof_unlocked_mev_reward,
            proof=self.proof,
        )

    @staticmethod
    def from_graph(vault_item: dict) -> 'Vault':
        vault_address = Web3.to_checksum_address(vault_item['id'])
        is_meta_vault = vault_item['isMetaVault']

        sub_vaults = [
            Web3.to_checksum_address(sub_vault['subVault']) for sub_vault in vault_item['subVaults']
        ]

        can_harvest = vault_item['canHarvest']

        # rewardsRoot
        is_meta_vault = vault_item['isMetaVault']

        sub_vaults = [
            Web3.to_checksum_address(sub_vault['subVault']) for sub_vault in vault_item['subVaults']
        ]

        can_harvest = vault_item['canHarvest']

        # rewardsRoot
        if vault_item['rewardsRoot'] is None:
            rewards_root = HexBytes(b'\x00' * 32)
        else:
            rewards_root = HexBytes(Web3.to_bytes(hexstr=vault_item['rewardsRoot']))

        # proofReward
        if vault_item['proofReward'] is None:
            proof_reward = Wei(0)
        else:
            proof_reward = Wei(int(vault_item['proofReward']))

        # proofUnlockedMevReward
        if vault_item['proofUnlockedMevReward'] is None:
            proof_unlocked_mev_reward = Wei(0)
        else:
            proof_unlocked_mev_reward = Wei(int(vault_item['proofUnlockedMevReward']))

        # proof
        if vault_item['proof'] is None:
            proof = []
        else:
            proof = [HexBytes(Web3.to_bytes(hexstr=p)) for p in vault_item['proof']]

        return Vault(
            address=vault_address,
            is_meta_vault=is_meta_vault,
            sub_vaults=sub_vaults,
            can_harvest=can_harvest,
            rewards_root=rewards_root,
            proof_reward=proof_reward,
            proof_unlocked_mev_reward=proof_unlocked_mev_reward,
            proof=proof,
        )
