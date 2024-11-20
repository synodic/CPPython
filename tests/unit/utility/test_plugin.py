"""This module tests the plugin functionality"""

from cppython.utility.plugin import Plugin


class MockPlugin(Plugin):
    """A mock plugin"""


class TestPlugin:
    """Tests the plugin functionality"""

    @staticmethod
    def test_plugin() -> None:
        """Test that the plugin functionality works"""
        assert MockPlugin.name() == 'mock'
        assert MockPlugin.group() == 'plugin'
