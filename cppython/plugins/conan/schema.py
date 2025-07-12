"""Conan plugin schema

This module defines Pydantic models used for integrating the Conan
package manager with the CPPython environment. The classes within
provide structured configuration and data needed by the Conan Provider.
"""

from typing import Annotated

from pydantic import Field

from cppython.core.schema import CPPythonModel


class ConanDependency(CPPythonModel):
    """Dependency information"""

    name: str
    version_ge: str | None = None
    include_prerelease: bool | None = None

    def requires(self) -> str:
        """Generate the requires attribute for Conan"""
        # TODO: Implement lower and upper bounds per conan documentation
        if self.version_ge:
            return f'{self.name}/[>={self.version_ge}]'
        return self.name


class ConanData(CPPythonModel):
    """Resolved conan data"""

    local: bool


class ConanConfiguration(CPPythonModel):
    """Raw conan data"""

    local: Annotated[bool, Field(description='Whether to publish packages locally without uploading to a remote')] = (
        False
    )
