"""Configuration loading and merging for CPPython

This module handles loading configuration from multiple sources:
1. Global configuration (~/.cppython/config.toml) - User-wide settings for all projects
2. Project configuration (pyproject.toml or cppython.toml) - Project-specific settings
3. Local overrides (.cppython.toml) - User-specific overrides, repository ignored

Local overrides (.cppython.toml) can override any field from both CPPythonLocalConfiguration
and CPPythonGlobalConfiguration. Validation occurs on the merged result, not on the override
file itself, allowing flexible user-specific customization.
"""

from pathlib import Path
from tomllib import loads
from typing import Any


class ConfigurationLoader:
    """Loads and merges CPPython configuration from multiple sources"""

    def __init__(self, project_root: Path) -> None:
        """Initialize the configuration loader

        Args:
            project_root: The root directory of the project
        """
        self.project_root = project_root
        self.pyproject_path = project_root / 'pyproject.toml'
        self.cppython_path = project_root / 'cppython.toml'
        self.local_override_path = project_root / '.cppython.toml'
        self.global_config_path = Path.home() / '.cppython' / 'config.toml'

    def load_pyproject_data(self) -> dict[str, Any]:
        """Load complete pyproject.toml data

        Returns:
            Dictionary containing the full pyproject.toml data

        Raises:
            FileNotFoundError: If pyproject.toml does not exist
        """
        if not self.pyproject_path.exists():
            raise FileNotFoundError(f'pyproject.toml not found at {self.pyproject_path}')

        return loads(self.pyproject_path.read_text(encoding='utf-8'))

    def load_cppython_config(self) -> dict[str, Any] | None:
        """Load CPPython configuration from cppython.toml if it exists

        Returns:
            Dictionary containing the cppython table data, or None if file doesn't exist
        """
        if not self.cppython_path.exists():
            return None

        data = loads(self.cppython_path.read_text(encoding='utf-8'))

        # Validate that it contains a cppython table
        if 'cppython' not in data:
            raise ValueError(f'{self.cppython_path} must contain a [cppython] table')

        return data['cppython']

    def load_global_config(self) -> dict[str, Any] | None:
        """Load global configuration from ~/.cppython/config.toml if it exists

        Returns:
            Dictionary containing the global configuration, or None if file doesn't exist
        """
        if not self.global_config_path.exists():
            return None

        data = loads(self.global_config_path.read_text(encoding='utf-8'))

        # Validate that it contains a cppython table
        if 'cppython' not in data:
            raise ValueError(f'{self.global_config_path} must contain a [cppython] table')

        return data['cppython']

    def load_local_overrides(self) -> dict[str, Any] | None:
        """Load local overrides from .cppython.toml if it exists

        These overrides have the highest priority and override both global
        and project configuration. This file should be gitignored as it
        contains machine-specific or user-specific settings.

        The override file can contain any fields from CPPythonLocalConfiguration
        or CPPythonGlobalConfiguration. Validation occurs on the merged result.

        Returns:
            Dictionary containing local override data, or None if file doesn't exist
        """
        if not self.local_override_path.exists():
            return None

        return loads(self.local_override_path.read_text(encoding='utf-8'))

    def merge_configurations(self, base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        """Deep merge two configuration dictionaries

        Args:
            base: Base configuration dictionary
            override: Override configuration dictionary

        Returns:
            Merged configuration with overrides taking precedence
        """
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Recursively merge nested dictionaries
                result[key] = self.merge_configurations(result[key], value)
            else:
                # Override value
                result[key] = value

        return result

    def load_cppython_table(self) -> dict[str, Any] | None:
        """Load and merge the CPPython configuration table from all sources

        Priority (highest to lowest):
        1. Local overrides (.cppython.toml) - Machine/user-specific settings
        2. Project configuration (pyproject.toml or cppython.toml) - Project-specific settings
        3. Global configuration (~/.cppython/config.toml) - User-wide defaults

        Returns:
            Merged CPPython configuration dictionary, or None if no config found
        """
        # Start with global configuration (lowest priority)
        result_config = self.load_global_config()

        # Load project configuration (pyproject.toml or cppython.toml)
        pyproject_data = self.load_pyproject_data()
        project_config = pyproject_data.get('tool', {}).get('cppython')

        # Try cppython.toml as alternative
        cppython_toml_config = self.load_cppython_config()
        if cppython_toml_config is not None:
            if project_config is not None:
                raise ValueError(
                    'CPPython configuration found in both pyproject.toml and cppython.toml. '
                    'Please use only one configuration source.'
                )
            project_config = cppython_toml_config

        # Merge project config over global config
        if project_config is not None and result_config is not None:
            result_config = self.merge_configurations(result_config, project_config)
        elif project_config is not None:
            result_config = project_config

        # Apply local overrides with highest priority
        local_overrides = self.load_local_overrides()
        if local_overrides is not None:
            if result_config is not None:
                result_config = self.merge_configurations(result_config, local_overrides)
            else:
                result_config = local_overrides

        return result_config

    def get_project_data(self) -> dict[str, Any]:
        """Get the complete pyproject data with merged CPPython configuration

        Returns:
            Dictionary containing pyproject data with merged tool.cppython table
        """
        pyproject_data = self.load_pyproject_data()

        # Load merged CPPython config
        cppython_config = self.load_cppython_table()

        # Update the pyproject data with merged config
        if cppython_config is not None:
            if 'tool' not in pyproject_data:
                pyproject_data['tool'] = {}
            pyproject_data['tool']['cppython'] = cppython_config

        return pyproject_data

    def config_source_info(self) -> dict[str, bool]:
        """Get information about which configuration files exist

        Returns:
            Dictionary with boolean flags for each config file's existence
        """
        return {
            'global_config': self.global_config_path.exists(),
            'pyproject': self.pyproject_path.exists(),
            'cppython': self.cppython_path.exists(),
            'local_overrides': self.local_override_path.exists(),
        }
