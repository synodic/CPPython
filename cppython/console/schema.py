"""Data definitions for the console application"""

from pydantic import ConfigDict

from cppython.core.interface import NoOpInterface
from cppython.core.schema import CPPythonModel, Interface, ProjectConfiguration

ConsoleInterface = NoOpInterface
"""Interface implementation for the console application (no-op write-backs)."""


class ConsoleConfiguration(CPPythonModel):
    """Configuration data for the console application"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    project_configuration: ProjectConfiguration
    interface: Interface
