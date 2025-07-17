"""Provides functionality to resolve Conan-specific data for the CPPython project."""

import logging
from typing import Any

from conan.api.conan_api import ConanAPI
from conan.internal.model.profile import Profile
from packaging.requirements import Requirement

from cppython.core.exception import ConfigException
from cppython.core.schema import CorePluginData
from cppython.plugins.conan.schema import ConanConfiguration, ConanData, ConanDependency
from cppython.utility.exception import ProviderConfigurationError


def _profile_post_process(profiles: list[Profile], conan_api: ConanAPI, cache_settings: Any) -> None:
    """Apply profile plugin and settings processing to a list of profiles.

    Args:
        profiles: List of profiles to process
        conan_api: The Conan API instance
        cache_settings: The settings configuration
    """
    logger = logging.getLogger('cppython.conan')

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

    # Process settings to initialize processed_settings
    for profile in profiles:
        try:
            profile.process_settings(cache_settings)
        except (AttributeError, Exception) as settings_error:
            logger.debug('Settings processing failed for profile: %s', str(settings_error))


def _resolve_profiles(
    host_profile_name: str | None, build_profile_name: str | None, conan_api: ConanAPI
) -> tuple[Profile, Profile]:
    """Resolve host and build profiles, with fallback to auto-detection.

    Args:
        host_profile_name: The host profile name to resolve, or None for auto-detection
        build_profile_name: The build profile name to resolve, or None for auto-detection
        conan_api: The Conan API instance

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
            return profile
        except Exception as e:
            logger.warning('Default %s profile not available, using auto-detection: %s', profile_type, str(e))

            # Create auto-detected profile
            profile = conan_api.profiles.detect()
            cache_settings = conan_api.config.settings_yml

            # Apply profile plugin processing
            _profile_post_process([profile], conan_api, cache_settings)

            logger.debug('Auto-detected %s profile with plugin processing applied', profile_type)
            return profile

    # Resolve both profiles
    host_profile = _resolve_profile(host_profile_name, is_host=True)
    build_profile = _resolve_profile(build_profile_name, is_host=False)

    return host_profile, build_profile


def resolve_conan_dependency(requirement: Requirement) -> ConanDependency:
    """Resolves a Conan dependency from a requirement"""
    specifiers = requirement.specifier

    # If the length of specifiers is greater than one, raise a configuration error
    if len(specifiers) > 1:
        raise ConfigException('Multiple specifiers are not supported. Please provide a single specifier.', [])

    # Extract the version from the single specifier
    min_version = None
    if len(specifiers) == 1:
        specifier = next(iter(specifiers))
        if specifier.operator != '>=':
            raise ConfigException(f"Unsupported specifier '{specifier.operator}'. Only '>=' is supported.", [])
        min_version = specifier.version

    return ConanDependency(
        name=requirement.name,
        version_ge=min_version,
    )


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

    # Resolve profiles
    host_profile, build_profile = _resolve_profiles(parsed_data.host_profile, parsed_data.build_profile, conan_api)

    return ConanData(
        remotes=parsed_data.remotes,
        host_profile=host_profile,
        build_profile=build_profile,
    )
