"""Test the functions related to the internal provider implementation and the 'Provider' interface itself"""

from typing import Any

import pytest
from pytest_mock import MockerFixture

from pytest_cppython.mock.generator import MockGenerator
from pytest_cppython.mock.provider import MockProvider
from pytest_cppython.tests import ProviderUnitTests


class TestMockProvider(ProviderUnitTests[MockProvider]):
    """The tests for our Mock provider"""

    @pytest.fixture(name="plugin_data", scope="session")
    def fixture_provider_data(self) -> dict[str, Any]:
        """Returns mock data

        Returns:
            An overridden data instance
        """

        return {}

    @pytest.fixture(name="plugin_type", scope="session")
    def fixture_plugin_type(self) -> type[MockProvider]:
        """A required testing hook that allows type generation

        Returns:
            An overridden provider type
        """
        return MockProvider

    def test_sync_types(self, plugin: MockProvider, mocker: MockerFixture) -> None:
        """Verify that the mock provider can handle the mock generator's sync data

        Args:
            plugin: The plugin instance
            mocker: The pytest-mock fixture
        """

        mock_generator = mocker.Mock(spec=MockGenerator)
        mock_generator.sync_types.return_value = MockGenerator.sync_types()

        assert plugin.sync_data(mock_generator)
