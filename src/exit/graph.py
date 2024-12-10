from typing import Any

from gql import gql
from graphql import DocumentNode
from web3 import Web3
from web3.types import BlockNumber, ChecksumAddress

from src.common.settings import GRAPH_PAGE_SIZE

from .clients import graph_client
from .typings import ExitRequest, LeveragePosition, OsTokenExitRequest


def paginate_query(query: DocumentNode, params: dict) -> list:
    res: list[Any] = []
    page_res = None
    first = GRAPH_PAGE_SIZE
    skip = 0

    while page_res is None or len(page_res):
        params['first'] = first
        params['skip'] = skip

        response = graph_client.execute(query, params)
        page_res = list(response.values())[0]

        skip += first
        res.extend(page_res)
    return res


def graph_get_leverage_positions(
    borrow_ltv: float, block_number: BlockNumber
) -> list[LeveragePosition]:
    query = gql(
        """
        query PositionsQuery($borrowLTV: String, $block: Int, $first: Int, $skip: Int) {
          leverageStrategyPositions(
            block: { number: $block },
            where: { borrowLtv_gt: $borrowLTV },
            orderBy: borrowLtv,
            orderDirection: desc,
            first: $first,
            skip: $skip
          ) {
            user
            proxy
            vault {
              id
            }
            exitRequest {
              id
              positionTicket
              timestamp
              exitQueueIndex
              isClaimable
              exitedAssets
              totalAssets
            }
          }
        }
        """
    )
    params = {'block': block_number, 'borrowLTV': str(borrow_ltv)}
    response = paginate_query(query, params)
    result = []
    for data in response:
        position = LeveragePosition(
            vault=Web3.to_checksum_address(data['vault']['id']),
            user=Web3.to_checksum_address(data['user']),
            proxy=Web3.to_checksum_address(data['proxy']),
        )
        if data['exitRequest']:
            position.exit_request = ExitRequest.from_graph(data['exitRequest'])

        result.append(position)
    return result


def graph_get_allocators(
    ltv: float, addresses: list[ChecksumAddress], block_number: BlockNumber
) -> list[ChecksumAddress]:
    query = gql(
        """
        query AllocatorsQuery(
          $ltv: String,
          $addresses: [String],
          $block: Int,
          $first: Int,
          $skip: Int
        ) {
          allocators(
            block: { number: $block },
            where: { ltv_gt: $ltv, address_in: $addresses },
            orderBy: ltv,
            orderDirection: desc,
            first: $first,
            skip: $skip
          ) {
            address
          }
        }
        """
    )
    params = {
        'ltv': str(ltv),
        'addresses': [address.lower() for address in addresses],
        'block': block_number,
    }
    response = paginate_query(query, params)
    result = []
    for data in response:
        result.append(
            Web3.to_checksum_address(data['address']),
        )
    return result


def graph_ostoken_exit_requests(ltv: int, block_number: BlockNumber) -> list[OsTokenExitRequest]:
    query = gql(
        """
        query ExitRequestsQuery($ltv: String, $block: Int, $first: Int, $skip: Int) {
          osTokenExitRequests(
            block: { number: $block },
            where: {ltv_gt: $ltv}
            first: $first
            skip: $skip
            ) {
            id
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
    response = paginate_query(query, params)

    exit_requests = graph_get_exit_requests(
        ids=[item['id'] for item in response], block_number=block_number
    )
    id_to_exit_request = {exit.id: exit for exit in exit_requests}

    result = []
    for data in response:
        result.append(
            OsTokenExitRequest(
                id=data['id'],
                vault=Web3.to_checksum_address(data['vault']['id']),
                owner=Web3.to_checksum_address(data['owner']),
                ltv=data['ltv'],
                exit_request=id_to_exit_request[data['id']],
            )
        )

    return result


def graph_get_exit_requests(ids: list[str], block_number: BlockNumber) -> list[ExitRequest]:
    query = gql(
        """
        query exitRequestQuery($ids: [String], $block: Int, $first: Int, $skip: Int) {
          exitRequests(
            block: { number: $block },
            where: { id_in: $ids },
            orderBy: id,
            first: $first,
            skip: $skip
          ) {
            id
            positionTicket
            timestamp
            exitQueueIndex
            isClaimable
            exitedAssets
            totalAssets
          }
        }
        """
    )
    params = {'block': block_number, 'ids': ids}
    response = paginate_query(query, params)
    result = []
    for data in response:
        result.append(ExitRequest.from_graph(data))
    return result
