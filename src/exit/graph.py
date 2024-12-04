from gql import gql
from web3 import Web3
from web3.types import BlockNumber, ChecksumAddress, Wei

from .clients import graph_client
from .typings import LeveragePosition, OsTokenExitRequest


def graph_get_leverage_positions(block_number: BlockNumber) -> list[LeveragePosition]:
    query = gql(
        """
        query PositionsQuery($block: BigInt) {
          leverageStrategyPositions(
            block: { number: $block },
            orderBy: borrowLtv,
            orderDirection: desc
          ) {
            user
            proxy
            vault {
              id
            }
          }
        }
        """
    )
    params = {'block': block_number}
    response = graph_client.execute(query, params)
    result = []
    for data in response['leverageStrategyPositions']:  # pylint: disable=unsubscriptable-object
        result.append(
            LeveragePosition(
                vault=Web3.to_checksum_address(data['vault']['id']),
                user=Web3.to_checksum_address(data['user']),
                proxy=Web3.to_checksum_address(data['proxy']),
            )
        )
    return result


def graph_get_allocators(
    addresses: list[ChecksumAddress], block_number: BlockNumber
) -> list[ChecksumAddress]:
    query = gql(
        """
        query AllocatorsQuery($addresses: [String], $block: BigInt) {
          allocators(
            block: { number: $block },
            where: {address_in: $addresses},
            orderBy: ltv,
            orderDirection: desc
          ) {
            address
          }
        }
        """
    )
    params = {'addresses': [address.lower() for address in addresses], 'block': block_number}
    response = graph_client.execute(query, params)
    result = []
    for data in response['allocators']:  # pylint: disable=unsubscriptable-object
        result.append(
            Web3.to_checksum_address(data['address']),
        )
    return result


def graph_ostoken_exit_requests(ltv: int, block_number: BlockNumber) -> list[OsTokenExitRequest]:
    query = gql(
        """
        query ExitRequestsQuery($ltv: String, $block: BigInt) {
          osTokenExitRequests(
            block: { number: $block },
            where: {ltv_gt: $ltv}
            ) {
            owner
            ltv
            positionTicket
            osTokenShares
            vault {
              id
            }
          }
        }
        """
    )
    params = {'ltv': str(ltv), 'block': block_number}
    response = graph_client.execute(query, params)
    result = []
    for data in response['osTokenExitRequests']:  # pylint: disable=unsubscriptable-object
        result.append(
            OsTokenExitRequest(
                vault=Web3.to_checksum_address(data['vault']['id']),
                owner=Web3.to_checksum_address(data['owner']),
                os_token_shares=Wei(int(data['osTokenShares'])),
                ltv=data['ltv'],
                position_ticket=int(data['positionTicket']),
            )
        )
    return result
