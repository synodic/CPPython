"""Definitions for the plugin"""

from pathlib import Path
from typing import Annotated

from pydantic import Field, HttpUrl
from pydantic.types import DirectoryPath

from cppython.core.schema import CPPythonModel


class VcpkgDependency(CPPythonModel):
    """Vcpkg dependency type"""

    name: str


class VcpkgData(CPPythonModel):
    """Resolved vcpkg data"""

    install_directory: DirectoryPath
    dependencies: list[VcpkgDependency]


class VcpkgConfiguration(CPPythonModel):
    """vcpkg provider data"""

    install_directory: Annotated[
        Path,
        Field(
            alias='install-directory',
            description='The referenced dependencies defined by the local vcpkg.json manifest file',
        ),
    ] = Path('build')

    dependencies: Annotated[
        list[VcpkgDependency], Field(description='The directory to store the manifest file, vcpkg.json')
    ] = []


class Manifest(CPPythonModel):
    """The manifest schema"""

    name: Annotated[str, Field(description='The project name')]

    version_string: Annotated[str, Field(alias='version-string', description='The arbitrary version string')] = ''

    homepage: Annotated[HttpUrl | None, Field(description='Homepage URL')] = None
    dependencies: Annotated[list[VcpkgDependency], Field(description='List of dependencies')] = []
