"""Configuration loading and merging for CPPython

This module handles loading configuration from multiple sources:
1. Global configuration (~/.cppython/config.toml) - User-wide settings for all projects
2. Project configuration (pyproject.toml or cppython.toml) - Project-specific settings
3. Local overrides (.cppython.toml) - Overrides for global configuration
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

        These overrides only affect the global configuration, not project configuration.

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
        1. Project configuration (pyproject.toml or cppython.toml)
        2. Local overrides (.cppython.toml) merged with global config
        3. Global configuration (~/.cppython/config.toml)

        Returns:
            Merged CPPython configuration dictionary, or None if no config found
        """
        # Start with global configuration
        global_config = self.load_global_config()

        # Apply local overrides to global config
        local_overrides = self.load_local_overrides()
        if local_overrides is not None and global_config is not None:
            global_config = self.merge_configurations(global_config, local_overrides)
        elif local_overrides is not None and global_config is None:
            # Local overrides exist but no global config - use overrides as base
            global_config = local_overrides

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

        # Merge: global config (with local overrides) + project config
        # Project config has highest priority
        if project_config is not None and global_config is not None:
            return self.merge_configurations(global_config, project_config)
        elif project_config is not None:
            return project_config
        elif global_config is not None:
            return global_config

        return None

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
