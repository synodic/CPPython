"""Definitions for the plugin"""
from pathlib import Path

from cppython_core.schema import CPPythonModel
from pydantic import Field, HttpUrl
from pydantic.types import DirectoryPath


class VcpkgDependency(CPPythonModel):
    """Vcpkg dependency type"""

    name: str


class VcpkgData(CPPythonModel):
    """Resolved vcpkg data"""

    install_directory: DirectoryPath
    dependencies: list[VcpkgDependency]


class VcpkgConfiguration(CPPythonModel):
    """vcpkg provider data"""

    install_directory: Path = Field(
        default=Path("build"),
        alias="install-directory",
        description="The referenced dependencies defined by the local vcpkg.json manifest file",
    )

    dependencies: list[VcpkgDependency] = Field(
        default=[], description="The directory to store the manifest file, vcpkg.json"
    )


class Manifest(CPPythonModel):
    """The manifest schema"""

    name: str = Field(description="The project name")

    version_string: str = Field(default="", alias="version-string", description="The arbitrary version string")
    homepage: HttpUrl | None = Field(default=None, description="Homepage URL")
    dependencies: list[VcpkgDependency] = Field(default=[], description="List of dependencies")
