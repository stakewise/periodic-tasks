from contextlib import contextmanager
from unittest import mock

from eth_typing import ChecksumAddress
from sw_utils.graph import GraphClient

from periodic_tasks.common.typings import Vault
from periodic_tasks.meta_vault.tasks import _get_meta_vault_tree_update_state_calls
from periodic_tasks.meta_vault.tests.factories import create_vault


class TestMetaVaultTreeUpdateStateCalls:
    async def test_basic(self):
        # Arrange
        meta_vault = create_vault(is_meta_vault=True, sub_vaults_count=2)
        sub_vault_0 = create_vault(address=meta_vault.sub_vaults[0])
        sub_vault_1 = create_vault(address=meta_vault.sub_vaults[1])
        meta_vaults_map = {
            meta_vault.address: meta_vault,
        }
        vaults_updated = set()
        graph_mock = GraphMock(
            [
                meta_vault,
                sub_vault_0,
                sub_vault_1,
            ]
        )

        # Act
        with self.patch(graph_mock=graph_mock):
            calls = await _get_meta_vault_tree_update_state_calls(
                root_meta_vault=meta_vault,
                meta_vaults_map=meta_vaults_map,
                vaults_updated=vaults_updated,
            )

        # Assert
        assert len(calls) == 3
        assert calls[0].address == meta_vault.sub_vaults[0]
        assert calls[1].address == meta_vault.sub_vaults[1]
        assert calls[2].address == meta_vault.address
        assert vaults_updated == {meta_vault.address, *meta_vault.sub_vaults}

    async def test_meta_vault_already_updated(self):
        # Arrange
        meta_vault = create_vault(is_meta_vault=True, sub_vaults_count=2)
        sub_vault_0 = create_vault(address=meta_vault.sub_vaults[0])
        sub_vault_1 = create_vault(address=meta_vault.sub_vaults[1])
        meta_vaults_map = {
            meta_vault.address: meta_vault,
        }
        graph_mock = GraphMock(
            [
                meta_vault,
                sub_vault_0,
                sub_vault_1,
            ]
        )
        vaults_updated = {meta_vault.address, *meta_vault.sub_vaults}

        # Act
        with self.patch(graph_mock=graph_mock):
            calls = await _get_meta_vault_tree_update_state_calls(
                root_meta_vault=meta_vault,
                meta_vaults_map=meta_vaults_map,
                vaults_updated=vaults_updated,
            )

        # Assert
        assert len(calls) == 0
        assert vaults_updated == {meta_vault.address, *meta_vault.sub_vaults}

    async def test_sub_vault_already_updated(self):
        # Arrange
        meta_vault = create_vault(is_meta_vault=True, sub_vaults_count=2)
        sub_vault_0 = create_vault(address=meta_vault.sub_vaults[0])
        sub_vault_1 = create_vault(address=meta_vault.sub_vaults[1])
        meta_vaults_map = {
            meta_vault.address: meta_vault,
        }
        graph_mock = GraphMock(
            [
                meta_vault,
                sub_vault_0,
                sub_vault_1,
            ]
        )
        vaults_updated = {meta_vault.sub_vaults[0]}

        # Act
        with self.patch(graph_mock=graph_mock):
            calls = await _get_meta_vault_tree_update_state_calls(
                root_meta_vault=meta_vault,
                meta_vaults_map=meta_vaults_map,
                vaults_updated=vaults_updated,
            )

        # Assert
        assert len(calls) == 2
        assert calls[0].address == meta_vault.sub_vaults[1]
        assert calls[1].address == meta_vault.address
        assert vaults_updated == {meta_vault.address, *meta_vault.sub_vaults}

    async def test_nested_meta_vault_basic(self):
        # Arrange
        meta_vault = create_vault(is_meta_vault=True, sub_vaults_count=2)

        # sub vault 0 is meta vault, sub vault 1 is regular vault
        sub_vault_0 = create_vault(
            address=meta_vault.sub_vaults[0], is_meta_vault=True, sub_vaults_count=2
        )
        sub_vault_1 = create_vault(address=meta_vault.sub_vaults[1])

        # sub vaults of sub vault 0
        sub_vault_2 = create_vault(address=sub_vault_0.sub_vaults[0])
        sub_vault_3 = create_vault(address=sub_vault_0.sub_vaults[1])

        meta_vaults_map = {
            meta_vault.address: meta_vault,
            sub_vault_0.address: sub_vault_0,
        }
        vaults_updated = set()
        graph_mock = GraphMock(
            [
                meta_vault,
                sub_vault_0,
                sub_vault_1,
                sub_vault_2,
                sub_vault_3,
            ]
        )

        # Act
        with self.patch(graph_mock=graph_mock):
            calls = await _get_meta_vault_tree_update_state_calls(
                root_meta_vault=meta_vault,
                meta_vaults_map=meta_vaults_map,
                vaults_updated=vaults_updated,
            )

        # Assert
        assert [c.address for c in calls] == [
            sub_vault_2.address,
            sub_vault_3.address,
            sub_vault_0.address,
            sub_vault_1.address,
            meta_vault.address,
        ]
        assert vaults_updated == {
            meta_vault.address,
            *meta_vault.sub_vaults,
            *sub_vault_0.sub_vaults,
        }

    async def test_nested_meta_vault_already_updated(self):
        # Arrange
        meta_vault = create_vault(is_meta_vault=True, sub_vaults_count=2)

        # sub vault 0 is meta vault, sub vault 1 is regular vault
        sub_vault_0 = create_vault(
            address=meta_vault.sub_vaults[0], is_meta_vault=True, sub_vaults_count=2
        )
        sub_vault_1 = create_vault(address=meta_vault.sub_vaults[1])

        # sub vaults of sub vault 0
        sub_vault_2 = create_vault(address=sub_vault_0.sub_vaults[0])
        sub_vault_3 = create_vault(address=sub_vault_0.sub_vaults[1])

        meta_vaults_map = {
            meta_vault.address: meta_vault,
            sub_vault_0.address: sub_vault_0,
        }
        graph_mock = GraphMock(
            [
                meta_vault,
                sub_vault_0,
                sub_vault_1,
                sub_vault_2,
                sub_vault_3,
            ]
        )
        vaults_updated = {sub_vault_0.address, *sub_vault_0.sub_vaults}

        # Act
        with self.patch(graph_mock=graph_mock):
            calls = await _get_meta_vault_tree_update_state_calls(
                root_meta_vault=meta_vault,
                meta_vaults_map=meta_vaults_map,
                vaults_updated=vaults_updated,
            )

        # Assert
        assert [c.address for c in calls] == [sub_vault_1.address, meta_vault.address]
        assert vaults_updated == {
            meta_vault.address,
            *meta_vault.sub_vaults,
            *sub_vault_0.sub_vaults,
        }

    async def test_sub_vault_level_2_already_updated(self):
        # Arrange
        meta_vault = create_vault(is_meta_vault=True, sub_vaults_count=2)

        # sub vault 0 is meta vault, sub vault 1 is regular vault
        sub_vault_0 = create_vault(
            address=meta_vault.sub_vaults[0], is_meta_vault=True, sub_vaults_count=2
        )
        sub_vault_1 = create_vault(address=meta_vault.sub_vaults[1])

        # sub vaults of sub vault 0
        sub_vault_2 = create_vault(address=sub_vault_0.sub_vaults[0])
        sub_vault_3 = create_vault(address=sub_vault_0.sub_vaults[1])

        meta_vaults_map = {
            meta_vault.address: meta_vault,
            sub_vault_0.address: sub_vault_0,
        }
        graph_mock = GraphMock(
            [
                meta_vault,
                sub_vault_0,
                sub_vault_1,
                sub_vault_2,
                sub_vault_3,
            ]
        )
        vaults_updated = {sub_vault_2.address}

        # Act
        with self.patch(graph_mock=graph_mock):
            calls = await _get_meta_vault_tree_update_state_calls(
                root_meta_vault=meta_vault,
                meta_vaults_map=meta_vaults_map,
                vaults_updated=vaults_updated,
            )

        # Assert
        assert [c.address for c in calls] == [
            sub_vault_3.address,
            sub_vault_0.address,
            sub_vault_1.address,
            meta_vault.address,
        ]
        assert vaults_updated == {
            meta_vault.address,
            *meta_vault.sub_vaults,
            *sub_vault_0.sub_vaults,
        }

    @contextmanager
    def patch(self, graph_mock: 'GraphMock'):
        with mock.patch(
            'periodic_tasks.meta_vault.tasks.graph_get_vaults',
            graph_mock.graph_get_vaults,
        ), mock.patch(
            'periodic_tasks.meta_vault.tasks.get_claimable_sub_vault_exit_requests', return_value=[]
        ), mock.patch(
            'periodic_tasks.meta_vault.tasks.is_meta_vault_rewards_nonce_outdated',
            return_value=False,
        ):
            yield


class GraphMock:
    def __init__(self, vaults: list[ChecksumAddress]):
        self._vaults = {vault.address: vault for vault in vaults}

    async def graph_get_vaults(
        self, graph_client: GraphClient, vaults: list[ChecksumAddress]
    ) -> dict[ChecksumAddress, Vault]:
        """
        Simulate fetching vaults from the graph
        """
        res = {}
        for vault_address in vaults:
            if vault_address not in self._vaults:
                continue
            res[vault_address] = self._vaults[vault_address]

        return res
