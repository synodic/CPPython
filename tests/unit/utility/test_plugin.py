"""This module tests the plugin functionality"""

from synodic_utilities.plugin import Plugin


class MockPlugin(Plugin):
    """A mock plugin"""


class TestPlugin:
    """Tests the plugin functionality"""

    def test_plugin(self) -> None:
        """Test that the plugin functionality works"""

        assert MockPlugin.name() == "mock"
        assert MockPlugin.group() == "plugin"

    def test_todo(self) -> None:
        """Another test TODO"""
