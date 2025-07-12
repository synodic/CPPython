"""Test integrations related to the internal provider implementation.

Test integrations related to the internal provider implementation and the
'Provider' interface itself.
"""

from typing import Any

import pytest

from cppython.test.mock.provider import MockProvider
from cppython.test.pytest.contracts import ProviderIntegrationTestContract


class TestMockProvider(ProviderIntegrationTestContract[MockProvider]):
    """The tests for our Mock provider"""

    @staticmethod
    @pytest.fixture(name='plugin_data', scope='session')
    def fixture_plugin_data() -> dict[str, Any]:
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
            The overridden provider type
        """
        return MockProvider
