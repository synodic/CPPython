"""Provides functionality to resolve Conan-specific data for the CPPython project."""

from pathlib import Path
from typing import Any

from packaging.requirements import Requirement

from cppython.core.exception import ConfigException
from cppython.core.schema import CorePluginData
from cppython.plugins.conan.schema import (
    ConanConfiguration,
    ConanData,
    ConanDependency,
    ConanVersion,
    ConanVersionRange,
)


def _handle_single_specifier(name: str, specifier) -> ConanDependency:
    """Handle a single version specifier."""
    MINIMUM_VERSION_PARTS = 2

    operator_handlers = {
        '==': lambda v: ConanDependency(name=name, version=ConanVersion.from_string(v)),
        '>=': lambda v: ConanDependency(name=name, version_range=ConanVersionRange(expression=f'>={v}')),
        '>': lambda v: ConanDependency(name=name, version_range=ConanVersionRange(expression=f'>{v}')),
        '<': lambda v: ConanDependency(name=name, version_range=ConanVersionRange(expression=f'<{v}')),
        '<=': lambda v: ConanDependency(name=name, version_range=ConanVersionRange(expression=f'<={v}')),
        '!=': lambda v: ConanDependency(name=name, version_range=ConanVersionRange(expression=f'!={v}')),
    }

    if specifier.operator in operator_handlers:
        return operator_handlers[specifier.operator](specifier.version)
    elif specifier.operator == '~=':
        # Compatible release - convert to Conan tilde syntax
        version_parts = specifier.version.split('.')
        if len(version_parts) >= MINIMUM_VERSION_PARTS:
            conan_version = '.'.join(version_parts[:MINIMUM_VERSION_PARTS])
            return ConanDependency(name=name, version_range=ConanVersionRange(expression=f'~{conan_version}'))
        else:
            return ConanDependency(name=name, version_range=ConanVersionRange(expression=f'>={specifier.version}'))
    else:
        raise ConfigException(
            f"Unsupported single specifier '{specifier.operator}'. Supported: '==', '>=', '>', '<', '<=', '!=', '~='",
            [],
        )


def resolve_conan_dependency(requirement: Requirement) -> ConanDependency:
    """Resolves a Conan dependency from a Python requirement string.

    Converts Python packaging requirements to Conan version specifications:
    - package>=1.0.0 -> package/[>=1.0.0]
    - package==1.0.0 -> package/1.0.0
    - package~=1.2.0 -> package/[~1.2]
    - package>=1.0,<2.0 -> package/[>=1.0 <2.0]
    """
    specifiers = requirement.specifier

    # Handle no version specifiers
    if not specifiers:
        return ConanDependency(name=requirement.name)

    # Handle single specifier (most common case)
    if len(specifiers) == 1:
        return _handle_single_specifier(requirement.name, next(iter(specifiers)))

    # Handle multiple specifiers - convert to Conan range syntax
    range_parts: list[str] = []

    # Define order for operators to ensure consistent output
    operator_order = ['>=', '>', '<=', '<', '!=']

    # Group specifiers by operator to ensure consistent ordering
    specifier_groups = {op: [] for op in operator_order}

    for specifier in specifiers:
        if specifier.operator in ('>=', '>', '<', '<=', '!='):
            specifier_groups[specifier.operator].append(specifier.version)
        elif specifier.operator == '==':
            # Multiple == operators would be contradictory
            raise ConfigException(
                "Multiple '==' specifiers are contradictory. Use a single '==' or range operators.", []
            )
        elif specifier.operator == '~=':
            # ~= with other operators is complex, for now treat as >=
            specifier_groups['>='].append(specifier.version)
        else:
            raise ConfigException(
                f"Unsupported specifier '{specifier.operator}' in multi-specifier requirement. "
                f"Supported: '>=', '>', '<', '<=', '!='",
                [],
            )

    # Build range parts in consistent order
    for operator in operator_order:
        for version in specifier_groups[operator]:
            range_parts.append(f'{operator}{version}')

    # Join range parts with spaces (Conan AND syntax)
    version_range = ' '.join(range_parts)
    return ConanDependency(name=requirement.name, version_range=ConanVersionRange(expression=version_range))


def resolve_conan_data(data: dict[str, Any], core_data: CorePluginData) -> ConanData:
    """Resolves the conan data

    Args:
        data: The data to resolve
        core_data: The core plugin data

    Returns:
        The resolved conan data
    """
    parsed_data = ConanConfiguration(**data)

    profile_dir = Path(parsed_data.profile_dir)

    if not profile_dir.is_absolute():
        profile_dir = core_data.cppython_data.tool_path / profile_dir

    return ConanData(
        remotes=parsed_data.remotes,
        skip_upload=parsed_data.skip_upload,
        profile_dir=profile_dir,
    )
