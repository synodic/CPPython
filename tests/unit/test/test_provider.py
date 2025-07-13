"""Test functions related to the internal provider implementation.

Test functions related to the internal provider implementation and the
'Provider' interface itself.
"""

from typing import Any

import pytest
from pytest_mock import MockerFixture

from cppython.test.mock.generator import MockGenerator
from cppython.test.mock.provider import MockProvider
from cppython.test.pytest.contracts import ProviderUnitTestContract


class TestMockProvider(ProviderUnitTestContract[MockProvider]):
    """The tests for our Mock provider"""

    @staticmethod
    @pytest.fixture(name='plugin_data', scope='session')
    def fixture_provider_data() -> dict[str, Any]:
        """Returns mock data

        Returns:
            An overridden data instance
        """
        return {}

    @staticmethod
    @pytest.fixture(name='plugin_type', scope='session')
    def fixture_plugin_type() -> type[MockProvider]:
        """A required testing hook that allows type generation

        Returns:
            An overridden provider type
        """
        return MockProvider

    @staticmethod
    def test_sync_types(plugin: MockProvider, mocker: MockerFixture) -> None:
        """Verify that the mock provider can handle the mock generator's sync data

        Args:
            plugin: The plugin instance
            mocker: The pytest-mock fixture
        """
        mock_generator = mocker.Mock(spec=MockGenerator)
        mock_generator.sync_types.return_value = MockGenerator.sync_types()

        assert plugin.sync_data(mock_generator)
