"""Provides functionality to resolve Conan-specific data for the CPPython project."""

import importlib
import logging
from pathlib import Path
from typing import Any

from conan.api.conan_api import ConanAPI
from conan.internal.model.profile import Profile
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
from cppython.utility.exception import ProviderConfigurationError


def _detect_cmake_program() -> str | None:
    """Detect CMake program path from the cmake module if available.

    Returns:
        Path to cmake executable, or None if not found
    """
    try:
        # Try to import cmake module and get its executable path
        # Note: cmake is an optional dependency, so we import it conditionally
        cmake = importlib.import_module('cmake')

        cmake_bin_dir = Path(cmake.CMAKE_BIN_DIR)

        # Try common cmake executable names (pathlib handles platform differences)
        for cmake_name in ['cmake.exe', 'cmake']:
            cmake_exe = cmake_bin_dir / cmake_name
            if cmake_exe.exists():
                return str(cmake_exe)

        return None
    except ImportError:
        # cmake module not available
        return None
    except (AttributeError, Exception):
        # If cmake module doesn't have expected attributes
        return None


def _profile_post_process(
    profiles: list[Profile], conan_api: ConanAPI, cache_settings: Any, cmake_program: str | None = None
) -> None:
    """Apply profile plugin and settings processing to a list of profiles.

    Args:
        profiles: List of profiles to process
        conan_api: The Conan API instance
        cache_settings: The settings configuration
        cmake_program: Optional path to cmake program to configure in profiles
    """
    logger = logging.getLogger('cppython.conan')

    # Get global configuration
    global_conf = conan_api.config.global_conf

    # Apply profile plugin processing
    try:
        profile_plugin = conan_api.profiles._load_profile_plugin()
        if profile_plugin is not None:
            for profile in profiles:
                try:
                    profile_plugin(profile)
                except Exception as plugin_error:
                    logger.warning('Profile plugin failed for profile: %s', str(plugin_error))
    except (AttributeError, Exception):
        logger.debug('Profile plugin not available or failed to load')

    # Apply the full profile processing pipeline for each profile
    for profile in profiles:
        # Set cmake program configuration if provided
        if cmake_program is not None:
            try:
                # Set the tools.cmake:cmake_program configuration in the profile
                profile.conf.update('tools.cmake:cmake_program', cmake_program)
                logger.debug('Set tools.cmake:cmake_program=%s in profile', cmake_program)
            except (AttributeError, Exception) as cmake_error:
                logger.debug('Failed to set cmake program configuration: %s', str(cmake_error))

        # Process settings to initialize processed_settings
        try:
            profile.process_settings(cache_settings)
        except (AttributeError, Exception) as settings_error:
            logger.debug('Settings processing failed for profile: %s', str(settings_error))

        # Validate configuration
        try:
            profile.conf.validate()
        except (AttributeError, Exception) as conf_error:
            logger.debug('Configuration validation failed for profile: %s', str(conf_error))

        # Apply global configuration to the profile
        try:
            if global_conf is not None:
                profile.conf.rebase_conf_definition(global_conf)
        except (AttributeError, Exception) as rebase_error:
            logger.debug('Configuration rebase failed for profile: %s', str(rebase_error))


def _apply_cmake_config_to_profile(profile: Profile, cmake_program: str | None, profile_type: str) -> None:
    """Apply cmake program configuration to a profile.

    Args:
        profile: The profile to configure
        cmake_program: Path to cmake program to configure
        profile_type: Type of profile (for logging)
    """
    if cmake_program is not None:
        logger = logging.getLogger('cppython.conan')
        try:
            profile.conf.update('tools.cmake:cmake_program', cmake_program)
            logger.debug('Set tools.cmake:cmake_program=%s in %s profile', cmake_program, profile_type)
        except (AttributeError, Exception) as cmake_error:
            logger.debug('Failed to set cmake program in %s profile: %s', profile_type, str(cmake_error))


def _resolve_profiles(
    host_profile_name: str | None, build_profile_name: str | None, conan_api: ConanAPI, cmake_program: str | None = None
) -> tuple[Profile, Profile]:
    """Resolve host and build profiles, with fallback to auto-detection.

    Args:
        host_profile_name: The host profile name to resolve, or None for auto-detection
        build_profile_name: The build profile name to resolve, or None for auto-detection
        conan_api: The Conan API instance
        cmake_program: Optional path to cmake program to configure in profiles

    Returns:
        A tuple of (host_profile, build_profile)
    """
    logger = logging.getLogger('cppython.conan')

    def _resolve_profile(profile_name: str | None, is_host: bool) -> Profile:
        """Helper to resolve a single profile."""
        profile_type = 'host' if is_host else 'build'

        if profile_name is not None and profile_name != 'default':
            # Explicitly specified profile name (not the default) - fail if not found
            try:
                logger.debug('Loading %s profile: %s', profile_type, profile_name)
                profile = conan_api.profiles.get_profile([profile_name])
                logger.debug('Successfully loaded %s profile: %s', profile_type, profile_name)
                _apply_cmake_config_to_profile(profile, cmake_program, profile_type)
                return profile
            except Exception as e:
                logger.error('Failed to load %s profile %s: %s', profile_type, profile_name, str(e))
                raise ProviderConfigurationError(
                    'conan',
                    f'Failed to load {profile_type} profile {profile_name}: {str(e)}',
                    f'{profile_type}_profile',
                ) from e
        elif profile_name == 'default':
            # Try to load default profile, but fall back to auto-detection if it fails
            try:
                logger.debug('Loading %s profile: %s', profile_type, profile_name)
                profile = conan_api.profiles.get_profile([profile_name])
                logger.debug('Successfully loaded %s profile: %s', profile_type, profile_name)
                _apply_cmake_config_to_profile(profile, cmake_program, profile_type)
                return profile
            except Exception as e:
                logger.debug(
                    'Failed to load %s profile %s: %s. Falling back to auto-detection.',
                    profile_type,
                    profile_name,
                    str(e),
                )
                # Fall back to auto-detection

        try:
            if is_host:
                default_profile_path = conan_api.profiles.get_default_host()
            else:
                default_profile_path = conan_api.profiles.get_default_build()

            profile = conan_api.profiles.get_profile([default_profile_path])
            logger.debug('Using default %s profile', profile_type)
            _apply_cmake_config_to_profile(profile, cmake_program, profile_type)
            return profile
        except Exception as e:
            logger.warning('Default %s profile not available, using auto-detection: %s', profile_type, str(e))

            # Create auto-detected profile
            profile = conan_api.profiles.detect()
            cache_settings = conan_api.config.settings_yml

            # Apply profile plugin processing
            _profile_post_process([profile], conan_api, cache_settings, cmake_program)

            logger.debug('Auto-detected %s profile with plugin processing applied', profile_type)
            return profile

    # Resolve both profiles
    host_profile = _resolve_profile(host_profile_name, is_host=True)
    build_profile = _resolve_profile(build_profile_name, is_host=False)

    return host_profile, build_profile


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
    range_parts = []

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

    # Initialize Conan API for profile resolution
    conan_api = ConanAPI()

    # Try to detect cmake program path from current virtual environment
    cmake_program = _detect_cmake_program()

    # Resolve profiles
    host_profile, build_profile = _resolve_profiles(
        parsed_data.host_profile, parsed_data.build_profile, conan_api, cmake_program
    )

    return ConanData(
        remotes=parsed_data.remotes,
        host_profile=host_profile,
        build_profile=build_profile,
    )
