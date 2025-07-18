from collections import defaultdict

from eth_typing import BlockNumber, ChecksumAddress
from gql import gql
from web3 import Web3
from web3.types import Wei

from periodic_tasks.exit.typings import ExitRequest

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
                    version_gte: 3,
                    isClaimOnBehalfEnabled: true
                }
            ) {
                id
                vault {
                    id
                }
                shareHolders(where: {earnedVaultAssets_gt: 0}) {
                    address
                    shares
                    earnedVaultAssets
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
                earned_vault_assets=Wei(int(shareholder_item['earnedVaultAssets'])),
            )
            reward_splitter.shareholders.append(shareholder)
        reward_splitters.append(reward_splitter)

    return reward_splitters


async def graph_get_claimable_exit_requests(
    block_number: BlockNumber, receivers: list[ChecksumAddress]
) -> dict[ChecksumAddress, list[ExitRequest]]:
    """
    Returns dict{receiver: list[ExitRequest]}
    """
    query = gql(
        '''
        query Query($block: Int, $first: Int, $skip: Int, $receivers: [String]) {
            exitRequests(
                block: {number: $block},
                where: {
                    receiver_in: $receivers,
                    isClaimable: true,
                    isClaimed: false
                }
            ) {
                id
                isClaimable
                isClaimed
                positionTicket
                timestamp
                exitQueueIndex
                receiver
                totalAssets
                exitedAssets
                vault {
                  id
                }
            }
        }
    '''
    )
    params = {
        'block': block_number,
        'receivers': [rs.lower() for rs in receivers],
    }
    response = await graph_client.fetch_pages(query, params=params)

    exit_requests: dict[ChecksumAddress, list[ExitRequest]] = defaultdict(list)

    for exit_request_item in response:
        exit_request = ExitRequest.from_graph(exit_request_item)
        if exit_request.can_be_claimed:
            exit_requests[exit_request.receiver].append(exit_request)

    return exit_requests
