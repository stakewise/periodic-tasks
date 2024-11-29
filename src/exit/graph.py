import logging

from gql import gql
from web3 import Web3
from web3.types import Wei

from .clients import graph_client
from .typings import LeveragePosition, OsTokenExitRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def graph_get_leverage_positions() -> list[LeveragePosition]:
    query = gql(
        """
        query PositionsQuery {
          leverageStrategyPositions {
            user
            osTokenShares
            id
            proxy
            vault {
              id
            }
          }
        }
        """
    )

    response = graph_client.execute(query)
    result = []
    for data in response['leverageStrategyPositions']:  # pylint: disable=unsubscriptable-object
        result.append(
            LeveragePosition(
                vault=Web3.to_checksum_address(data['vault']['id']),
                user=Web3.to_checksum_address(data['user']),
            )
        )
    return result


def graph_osToken_exit_requests(ltv: str) -> list[OsTokenExitRequest]:
    query = gql(
        """
        query ExitRequestsQuery($ltv: String) {
          osTokenExitRequests(where: {ltv_gt: $ltv}) {
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
    params = {
        'ltv': ltv,
    }
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
