"""Definitions for the plugin"""

from pathlib import Path
from typing import Annotated

from pydantic import Field, HttpUrl

from cppython.core.schema import CPPythonModel


class VcpkgDependency(CPPythonModel):
    """Vcpkg dependency type"""

    name: Annotated[str, Field(description='The name of the dependency.')]
    default_features: Annotated[
        bool,
        Field(
            alias='default-features',
            description='Whether to use the default features of the dependency. Defaults to true.',
        ),
    ] = True
    features: Annotated[
        list[str],
        Field(description='A list of additional features to require for the dependency.'),
    ] = []
    version: Annotated[
        str | None,
        Field(
            description='The minimum required version of the dependency, optionally with a port-version suffix.',
        ),
    ] = None
    platform: Annotated[
        str | None,
        Field(description='A platform expression specifying the platforms where the dependency applies.'),
    ] = None
    host: Annotated[
        bool,
        Field(description='Whether the dependency is required for the host machine instead of the target.'),
    ] = False


class VcpkgData(CPPythonModel):
    """Resolved vcpkg data"""

    install_directory: Path
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


class Manifest(CPPythonModel):
    """The manifest schema"""

    name: Annotated[str, Field(description='The project name')]

    version_string: Annotated[str, Field(alias='version-string', description='The arbitrary version string')] = ''

    description: Annotated[str, Field(description='The project description')] = ''
    homepage: Annotated[HttpUrl | None, Field(description='Homepage URL')] = None
    dependencies: Annotated[list[VcpkgDependency], Field(description='List of dependencies')] = []
