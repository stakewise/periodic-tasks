from eth_typing import BlockNumber, ChecksumAddress
from gql import gql
from web3 import Web3

from .clients import graph_client
from .typings import RewardSplitter, RewardSplitterShareHolder


async def graph_get_reward_splitters(
    block_number: BlockNumber, vaults: list[ChecksumAddress]
) -> list[RewardSplitter]:
    query = gql(
        '''
        query Query($block: Int, $first: Int, $skip: Int, $vaults: [String]) {
            rewardSplitters(
                block: {number: $block},
                where: {
                    vault_in: $vaults,
                    isClaimOnBehalfEnabled: true
                }
            ) {
                id
                vault {
                    id
                }
                shareHolders(where: {shares_gt: 0}) {
                    address
                    shares
                }
            }
        }
    '''
    )
    params = {
        'block': block_number,
        'vaults': [v.lower() for v in vaults],
    }
    response = await graph_client.fetch_pages(query, params=params)
    reward_splitters = []

    for reward_splitter_item in response:
        reward_splitter = RewardSplitter(
            address=Web3.to_checksum_address(reward_splitter_item['id']),
            vault=Web3.to_checksum_address(reward_splitter_item['vault']['id']),
            shareholders=[],
        )
        for shareholder_item in reward_splitter_item['shareHolders']:
            shareholder = RewardSplitterShareHolder(
                address=Web3.to_checksum_address(shareholder_item['address']),
            )
            reward_splitter.shareholders.append(shareholder)
        reward_splitters.append(reward_splitter)

    return reward_splitters
