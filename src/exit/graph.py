from gql import gql
from sw_utils.networks import HOLESKY
from web3 import Web3
from web3.types import BlockNumber, ChecksumAddress

from src.common.graph import get_harvest_params
from src.common.settings import NETWORK
from src.common.typings import HarvestParams

from .clients import graph_client
from .typings import ExitRequest, LeveragePosition, OsTokenExitRequest

DISABLED_LIQ_THRESHOLD = 2**64 - 1
HOLESKY_UNCLAIMABLE_EXIT_REQUEST_IDS = [
    '0x8a94e1d22d83990205843cda08376d16f150c9bb-210258902756807306422',
    '0x8a94e1d22d83990205843cda08376d16f150c9bb-450147843736954431325',
    '0x8a94e1d22d83990205843cda08376d16f150c9bb-458856763747647876703',
    '0x8a94e1d22d83990205843cda08376d16f150c9bb-464067729736660634975',
    '0x8a94e1d22d83990205843cda08376d16f150c9bb-465799992852070364982',
]


async def graph_get_leverage_positions(block_number: BlockNumber) -> list[LeveragePosition]:
    query = gql(
        """
        query PositionsQuery($block: Int, $first: Int, $skip: Int) {
          leverageStrategyPositions(
            block: { number: $block },
            orderBy: borrowLtv,
            orderDirection: desc,
            first: $first,
            skip: $skip
          ) {
            user
            proxy
            borrowLtv
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
    params = {'block': block_number}
    response = await graph_client.fetch_pages(query, params=params)
    result = []
    for data in response:
        position = LeveragePosition(
            vault=Web3.to_checksum_address(data['vault']['id']),
            user=Web3.to_checksum_address(data['user']),
            proxy=Web3.to_checksum_address(data['proxy']),
            borrow_ltv=float(data['borrowLtv']),
        )
        if data['exitRequest']:
            position.exit_request = ExitRequest.from_graph(data['exitRequest'])

        result.append(position)
    return result


async def graph_get_allocators(
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
            vault {
              osTokenConfig {
                liqThresholdPercent
              }
            }
          }
        }
        """
    )
    params = {
        'ltv': str(ltv),
        'addresses': [address.lower() for address in addresses],
        'block': block_number,
    }
    response = await graph_client.fetch_pages(query, params=params)
    result = []
    for data in response:
        vault_liq_threshold = int(data['vault']['osTokenConfig']['liqThresholdPercent'])
        if vault_liq_threshold != DISABLED_LIQ_THRESHOLD:
            result.append(
                Web3.to_checksum_address(data['address']),
            )
    return result


async def graph_ostoken_exit_requests(
    ltv: float, block_number: BlockNumber
) -> list[OsTokenExitRequest]:
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
    response = await graph_client.fetch_pages(query, params=params)

    exit_requests = await graph_get_exit_requests(
        ids=[item['id'] for item in response], block_number=block_number
    )
    id_to_exit_request = {exit_req.id: exit_req for exit_req in exit_requests}

    result = []
    for data in response:
        if NETWORK == HOLESKY and data['id'] in HOLESKY_UNCLAIMABLE_EXIT_REQUEST_IDS:
            continue

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


async def graph_get_leverage_position_owner(proxy: ChecksumAddress) -> ChecksumAddress:
    query = gql(
        """
        query PositionsQuery($proxy: Bytes) {
          leverageStrategyPositions(where: { proxy: $proxy }) {
            user
          }
        }
        """
    )
    params = {'proxy': proxy.lower()}
    response = await graph_client.fetch_pages(query, params=params)
    return Web3.to_checksum_address(response[0]['user'])


async def graph_get_exit_requests(ids: list[str], block_number: BlockNumber) -> list[ExitRequest]:
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
    response = await graph_client.fetch_pages(query, params=params)
    result = []
    for data in response:
        result.append(ExitRequest.from_graph(data))
    return result


async def graph_get_harvest_params(vault_address: ChecksumAddress) -> HarvestParams | None:
    return await get_harvest_params(graph_client, vault_address)
