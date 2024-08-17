"""Unit tests for the interface
"""

import pytest
from pdm.core import Core
from pdm.project.core import Project

from cppython_pdm.plugin import CPPythonPlugin


class TestCPPythonInterface:
    """The tests for the PDM interface"""

    @pytest.fixture(name="interface")
    def fixture_interface(self, plugin_type: type[CPPythonPlugin]) -> CPPythonPlugin:
        """A hook allowing implementations to override the fixture

        Args:
            plugin_type: An input interface type

        Returns:
            A newly constructed interface
        """
        return plugin_type(Core())

    def test_pdm_project(self) -> None:
        """Verify that this PDM won't return empty data"""

        core = Core()
        core.load_plugins()
        pdm_project = Project(core, root_path=None)

        assert pdm_project
