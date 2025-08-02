"""Conan plugin schema

This module defines Pydantic models used for integrating the Conan
package manager with the CPPython environment. The classes within
provide structured configuration and data needed by the Conan Provider.
"""

import re
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator

from cppython.core.schema import CPPythonModel


class ConanVersion(CPPythonModel):
    """Represents a single Conan version with optional pre-release suffix."""

    major: int
    minor: int
    patch: int | None = None
    prerelease: str | None = None

    @field_validator('major', 'minor', mode='before')  # type: ignore
    @classmethod
    def validate_version_parts(cls, v: int) -> int:
        """Validate version parts are non-negative integers."""
        if v < 0:
            raise ValueError('Version parts must be non-negative')
        return v

    @field_validator('patch', mode='before')  # type: ignore
    @classmethod
    def validate_patch(cls, v: int | None) -> int | None:
        """Validate patch is non-negative integer or None."""
        if v is not None and v < 0:
            raise ValueError('Version parts must be non-negative')
        return v

    @field_validator('prerelease', mode='before')  # type: ignore
    @classmethod
    def validate_prerelease(cls, v: str | None) -> str | None:
        """Validate prerelease is not an empty string."""
        if v is not None and not v.strip():
            raise ValueError('Pre-release cannot be empty string')
        return v

    def __str__(self) -> str:
        """String representation of the version."""
        version = f'{self.major}.{self.minor}.{self.patch}' if self.patch is not None else f'{self.major}.{self.minor}'

        if self.prerelease:
            version += f'-{self.prerelease}'
        return version

    @classmethod
    def from_string(cls, version_str: str) -> 'ConanVersion':
        """Parse a version string into a ConanVersion."""
        if '-' in version_str:
            version_part, prerelease = version_str.split('-', 1)
        else:
            version_part = version_str
            prerelease = None

        parts = version_part.split('.')

        # Parse parts based on what's actually provided
        MAJOR_INDEX = 0
        MINOR_INDEX = 1
        PATCH_INDEX = 2

        major = int(parts[MAJOR_INDEX])
        minor = int(parts[MINOR_INDEX]) if len(parts) > MINOR_INDEX else 0
        patch = int(parts[PATCH_INDEX]) if len(parts) > PATCH_INDEX else None

        return cls(
            major=major,
            minor=minor,
            patch=patch,
            prerelease=prerelease,
        )


class ConanVersionRange(CPPythonModel):
    """Represents a Conan version range expression like '>=1.0 <2.0' or complex expressions."""

    expression: str

    @field_validator('expression')  # type: ignore
    @classmethod
    def validate_expression(cls, v: str) -> str:
        """Validate the version range expression contains valid operators."""
        if not v.strip():
            raise ValueError('Version range expression cannot be empty')

        # Basic validation - ensure it contains valid operators
        valid_operators = {'>=', '>', '<=', '<', '!=', '~', '||', '&&'}

        # Split by spaces and logical operators to get individual components
        tokens = re.split(r'(\|\||&&|\s+)', v)

        for token in tokens:
            current_token = token.strip()
            if not current_token or current_token in {'||', '&&'}:
                continue

            # Check if token starts with a valid operator
            has_valid_operator = any(current_token.startswith(op) for op in valid_operators)
            if not has_valid_operator:
                raise ValueError(f'Invalid operator in version range: {current_token}')

        return v

    def __str__(self) -> str:
        """Return the version range expression."""
        return self.expression


class ConanUserChannel(CPPythonModel):
    """Represents a Conan user/channel pair."""

    user: str
    channel: str | None = None

    @field_validator('user')  # type: ignore
    @classmethod
    def validate_user(cls, v: str) -> str:
        """Validate user is not empty."""
        if not v.strip():
            raise ValueError('User cannot be empty')
        return v.strip()

    @field_validator('channel')  # type: ignore
    @classmethod
    def validate_channel(cls, v: str | None) -> str | None:
        """Validate channel is not an empty string."""
        if v is not None and not v.strip():
            raise ValueError('Channel cannot be empty string')
        return v.strip() if v else None

    def __str__(self) -> str:
        """String representation for use in requires()."""
        if self.channel:
            return f'{self.user}/{self.channel}'
        return f'{self.user}/_'


class ConanRevision(CPPythonModel):
    """Represents a Conan revision identifier."""

    revision: str

    @field_validator('revision')  # type: ignore
    @classmethod
    def validate_revision(cls, v: str) -> str:
        """Validate revision is not empty."""
        if not v.strip():
            raise ValueError('Revision cannot be empty')
        return v.strip()

    def __str__(self) -> str:
        """Return the revision identifier."""
        return self.revision


class ConanDependency(CPPythonModel):
    """Dependency information following Conan's full version specification.

    Supports:
    - Exact versions: package/1.0.0
    - Pre-release versions: package/1.0.0-alpha1
    - Version ranges: package/[>1.0 <2.0]
    - Revisions: package/1.0.0#revision
    - User/channel: package/1.0.0@user/channel
    - Complex expressions: package/[>=1.0 <2.0 || >=3.0]
    - Pre-release handling: resolve_prereleases setting
    """

    name: str
    version: ConanVersion | None = None
    version_range: ConanVersionRange | None = None
    user_channel: ConanUserChannel | None = None
    revision: ConanRevision | None = None

    # Pre-release handling
    resolve_prereleases: bool | None = None

    def requires(self) -> str:
        """Generate the requires attribute for Conan following the full specification.

        Examples:
        - package -> package
        - package/1.0.0 -> package/1.0.0
        - package/1.0.0-alpha1 -> package/1.0.0-alpha1
        - package/[>=1.0 <2.0] -> package/[>=1.0 <2.0]
        - package/1.0.0@user/channel -> package/1.0.0@user/channel
        - package/1.0.0#revision -> package/1.0.0#revision
        - package/1.0.0@user/channel#revision -> package/1.0.0@user/channel#revision
        """
        result = self.name

        # Add version or version range
        if self.version_range:
            # Complex version range
            result += f'/[{self.version_range}]'
        elif self.version:
            # Simple version (can include pre-release suffixes)
            result += f'/{self.version}'

        # Add user/channel
        if self.user_channel:
            result += f'@{self.user_channel}'

        # Add revision
        if self.revision:
            result += f'#{self.revision}'

        return result

    @classmethod
    def from_conan_reference(cls, reference: str) -> 'ConanDependency':
        """Parse a Conan reference string into a ConanDependency.

        Examples:
        - package -> ConanDependency(name='package')
        - package/1.0.0 -> ConanDependency(name='package', version=ConanVersion.from_string('1.0.0'))
        - package/[>=1.0 <2.0] -> ConanDependency(name='package', version_range=ConanVersionRange('>=1.0 <2.0'))
        - package/1.0.0@user/channel -> ConanDependency(name='package', version=..., user_channel=ConanUserChannel(...))
        - package/1.0.0#revision -> ConanDependency(name='package', version=..., revision=ConanRevision('revision'))
        """
        # Split revision first (everything after #)
        revision_obj = None
        if '#' in reference:
            reference, revision_str = reference.rsplit('#', 1)
            revision_obj = ConanRevision(revision=revision_str)

        # Split user/channel (everything after @)
        user_channel_obj = None
        if '@' in reference:
            reference, user_channel_str = reference.rsplit('@', 1)
            if '/' in user_channel_str:
                user, channel = user_channel_str.split('/', 1)
                if channel == '_':
                    channel = None
            else:
                user = user_channel_str
                channel = None
            user_channel_obj = ConanUserChannel(user=user, channel=channel)

        # Split name and version
        name = reference
        version_obj = None
        version_range_obj = None

        if '/' in reference:
            name, version_part = reference.split('/', 1)

            # Check if it's a version range (enclosed in brackets)
            if version_part.startswith('[') and version_part.endswith(']'):
                version_range_obj = ConanVersionRange(expression=version_part[1:-1])  # Remove brackets
            else:
                version_obj = ConanVersion.from_string(version_part)

        return cls(
            name=name,
            version=version_obj,
            version_range=version_range_obj,
            user_channel=user_channel_obj,
            revision=revision_obj,
        )

    def is_prerelease(self) -> bool:
        """Check if this dependency specifies a pre-release version.

        Pre-release versions contain hyphens followed by pre-release identifiers
        like: 1.0.0-alpha1, 1.0.0-beta2, 1.0.0-rc1, 1.0.0-dev, etc.
        """
        # Check version object for pre-release
        if self.version and self.version.prerelease:
            prerelease_keywords = {'alpha', 'beta', 'rc', 'dev', 'pre', 'snapshot'}
            return any(keyword in self.version.prerelease.lower() for keyword in prerelease_keywords)

        # Also check version_range for pre-release patterns
        if self.version_range and '-' in self.version_range.expression:
            prerelease_keywords = {'alpha', 'beta', 'rc', 'dev', 'pre', 'snapshot'}
            return any(keyword in self.version_range.expression.lower() for keyword in prerelease_keywords)

        return False


class ConanData(CPPythonModel):
    """Resolved conan data"""

    remotes: list[str]
    skip_upload: bool
    profile_dir: Path


class ConanConfiguration(CPPythonModel):
    """Raw conan data"""

    remotes: Annotated[
        list[str],
        Field(description='List of remotes to upload to. If empty, uploads to all available remotes.'),
    ] = ['conancenter']
    skip_upload: Annotated[
        bool,
        Field(description='If true, skip uploading packages to a remote during publishing.'),
    ] = False
    profile_dir: Annotated[
        str,
        Field(
            description='Directory containing Conan profiles. Profiles will be looked up relative to this directory. '
            'If profiles do not exist in this directory, Conan will fall back to default profiles.'
            "If a relative path is provided, it will be resolved relative to the tool's working directory."
        ),
    ] = 'profiles'
