"""Plugin builder"""

from pathlib import Path

from cppython.plugins.cmake.schema import (
    BuildPreset,
    CMakeData,
    CMakePresets,
    CMakeSyncData,
    ConfigurePreset,
)


class Builder:
    """Aids in building the information needed for the CMake plugin"""

    def __init__(self) -> None:
        """Initialize the builder"""

    @staticmethod
    def generate_cppython_preset(
        cppython_preset_directory: Path, provider_preset_file: Path, provider_data: CMakeSyncData
    ) -> CMakePresets:
        """Generates the cppython preset which inherits from the provider presets

        Args:
            cppython_preset_directory: The tool directory
            provider_preset_file: Path to the provider's preset file
            provider_data: The provider's synchronization data

        Returns:
            A CMakePresets object
        """
        configure_presets = []

        preset_name = 'cppython-default'
        parent_preset_name = f'{provider_data.provider_name}-default'

        # Create a default preset that inherits from provider's default preset
        default_configure = ConfigurePreset(name=preset_name, inherits=parent_preset_name, hidden=True)
        configure_presets.append(default_configure)

        # Create presets for each configuration
        for config in provider_data.configurations:
            config_name = config.lower()
            preset_name = f'cppython-{config_name}'
            parent_preset_name = f'{provider_data.provider_name}-{config_name}'
            preset = ConfigurePreset(name=preset_name, inherits=parent_preset_name, hidden=True)
            configure_presets.append(preset)

        build_presets = []

        # Multi-config build presets using the default configure preset.
        # Important: Do not use a configure preset here, the user will do that in their own presets.
        for config in provider_data.configurations:
            config_name = config.lower()
            preset_name = f'cppython-multi-{config_name}'
            parent_preset_name = f'{provider_data.provider_name}-multi-{config_name}'
            multi_build_preset = BuildPreset(
                name=preset_name,
                configuration=config,
                inherits=parent_preset_name,
            )
            build_presets.append(multi_build_preset)

        # Single-config build presets using the config-specific configure presets
        # Important: Do not use a configure preset here, the user will do that in their own presets.
        for config in provider_data.configurations:
            config_name = config.lower()
            parent_config_name = f'{provider_data.provider_name}-{config_name}'
            single_build_preset = BuildPreset(
                name=config_name,
                configuration=config,
                inherits=parent_config_name,
            )
            build_presets.append(single_build_preset)

        generated_preset = CMakePresets(
            configurePresets=configure_presets,
            buildPresets=build_presets,
        )

        # Get the relative path to the provider preset file
        relative_preset = provider_preset_file.relative_to(cppython_preset_directory, walk_up=True).as_posix()

        # Set the data
        generated_preset.include = [relative_preset]
        return generated_preset

    @staticmethod
    def write_cppython_preset(
        cppython_preset_directory: Path, provider_preset_file: Path, provider_data: CMakeSyncData
    ) -> Path:
        """Write the cppython presets which inherit from the provider presets

        Args:
            cppython_preset_directory: The tool directory
            provider_preset_file: Path to the provider's preset file
            provider_data: The provider's synchronization data

        Returns:
            A file path to the written data
        """
        generated_preset = Builder.generate_cppython_preset(
            cppython_preset_directory, provider_preset_file, provider_data
        )
        cppython_preset_file = cppython_preset_directory / 'cppython.json'

        initial_preset = None

        # If the file already exists, we need to compare it
        if cppython_preset_file.exists():
            with open(cppython_preset_file, encoding='utf-8') as file:
                initial_json = file.read()
            initial_preset = CMakePresets.model_validate_json(initial_json)

        # Only write the file if the data has changed
        if generated_preset != initial_preset:
            serialized = generated_preset.model_dump_json(exclude_none=True, by_alias=False, indent=4)
            with open(cppython_preset_file, 'w', encoding='utf8') as file:
                file.write(serialized)

        return cppython_preset_file

    @staticmethod
    def _create_user_presets(cmake_data: CMakeData, build_directory: Path) -> tuple[ConfigurePreset, list[BuildPreset]]:
        """Create user configure and build presets.

        Args:
            cmake_data: The CMake data to use
            build_directory: The build directory to use

        Returns:
            A tuple containing the configure preset and list of build presets
        """
        user_configure_preset = ConfigurePreset(
            name=cmake_data.configuration_name,
            inherits='default',  # Inherit from cppython's default preset
            binaryDir=build_directory.as_posix(),
        )

        user_build_presets = [
            BuildPreset(
                name=f'{cmake_data.configuration_name}-multi-release',
                configurePreset=cmake_data.configuration_name,
                configuration='Release',
            ),
            BuildPreset(
                name=f'{cmake_data.configuration_name}-multi-debug',
                configurePreset=cmake_data.configuration_name,
                configuration='Debug',
            ),
        ]

        return user_configure_preset, user_build_presets

    @staticmethod
    def _load_existing_preset(preset_file: Path) -> CMakePresets | None:
        """Load existing preset file if it exists.

        Args:
            preset_file: Path to the preset file

        Returns:
            CMakePresets object if file exists, None otherwise
        """
        if not preset_file.exists():
            return None

        with open(preset_file, encoding='utf-8') as file:
            initial_json = file.read()
        return CMakePresets.model_validate_json(initial_json)

    @staticmethod
    def _update_configure_preset(existing_preset: ConfigurePreset, build_directory: Path) -> None:
        """Update an existing configure preset to ensure proper inheritance and binary directory.

        Args:
            existing_preset: The preset to update
            build_directory: The build directory to use
        """
        # Update existing preset to ensure it inherits from 'default'
        if existing_preset.inherits is None:
            existing_preset.inherits = 'default'  # type: ignore[misc]
        elif isinstance(existing_preset.inherits, str) and existing_preset.inherits != 'default':
            existing_preset.inherits = ['default', existing_preset.inherits]  # type: ignore[misc]
        elif isinstance(existing_preset.inherits, list) and 'default' not in existing_preset.inherits:
            existing_preset.inherits.insert(0, 'default')

        # Update binary directory if not set
        if not existing_preset.binaryDir:
            existing_preset.binaryDir = build_directory.as_posix()  # type: ignore[misc]

    @staticmethod
    def _handle_configure_presets(
        root_preset: CMakePresets, user_configure_preset: ConfigurePreset, build_directory: Path
    ) -> None:
        """Handle configure presets in the root preset.

        Args:
            root_preset: The root preset to modify
            user_configure_preset: The user's configure preset
            build_directory: The build directory to use
        """
        if root_preset.configurePresets is None:
            root_preset.configurePresets = [user_configure_preset]  # type: ignore[misc]
        else:
            # Update or add the user's configure preset
            existing_preset = next(
                (p for p in root_preset.configurePresets if p.name == user_configure_preset.name), None
            )
            if existing_preset:
                Builder._update_configure_preset(existing_preset, build_directory)
            else:
                root_preset.configurePresets.append(user_configure_preset)

    @staticmethod
    def _handle_build_presets(root_preset: CMakePresets, user_build_presets: list[BuildPreset]) -> None:
        """Handle build presets in the root preset.

        Args:
            root_preset: The root preset to modify
            user_build_presets: The user's build presets to add
        """
        if root_preset.buildPresets is None:
            root_preset.buildPresets = user_build_presets.copy()  # type: ignore[misc]
        else:
            # Add build presets if they don't exist
            for build_preset in user_build_presets:
                existing = next((p for p in root_preset.buildPresets if p.name == build_preset.name), None)
                if not existing:
                    root_preset.buildPresets.append(build_preset)

    @staticmethod
    def _handle_includes(root_preset: CMakePresets, preset_file: Path, cppython_preset_file: Path) -> None:
        """Handle include paths in the root preset.

        Args:
            root_preset: The root preset to modify
            preset_file: Path to the preset file
            cppython_preset_file: Path to the cppython preset file to include
        """
        # Get the relative path to the cppython preset file
        preset_directory = preset_file.parent.absolute()
        relative_preset = cppython_preset_file.relative_to(preset_directory, walk_up=True).as_posix()

        # Handle includes
        if not root_preset.include:
            root_preset.include = []  # type: ignore[misc]

        if str(relative_preset) not in root_preset.include:
            root_preset.include.append(str(relative_preset))

    @staticmethod
    def generate_root_preset(
        preset_file: Path, cppython_preset_file: Path, cmake_data: CMakeData, build_directory: Path
    ) -> CMakePresets:
        """Generates the top level root preset with the include reference.

        Args:
            preset_file: Preset file to modify
            cppython_preset_file: Path to the cppython preset file to include
            cmake_data: The CMake data to use
            build_directory: The build directory to use

        Returns:
            A CMakePresets object
        """
        # Create user presets
        user_configure_preset, user_build_presets = Builder._create_user_presets(cmake_data, build_directory)

        # Load existing preset or create new one
        root_preset = Builder._load_existing_preset(preset_file)
        if root_preset is None:
            root_preset = CMakePresets(
                configurePresets=[user_configure_preset],
                buildPresets=user_build_presets,
            )
        else:
            # Handle existing preset
            Builder._handle_configure_presets(root_preset, user_configure_preset, build_directory)
            Builder._handle_build_presets(root_preset, user_build_presets)

        # Handle includes
        Builder._handle_includes(root_preset, preset_file, cppython_preset_file)

        return root_preset

    @staticmethod
    def write_root_presets(
        preset_file: Path, cppython_preset_file: Path, cmake_data: CMakeData, build_directory: Path
    ) -> None:
        """Read the top level json file and insert the include reference.

        Receives a relative path to the tool cmake json file

        Raises:
            ConfigError: If key files do not exists

        Args:
            preset_file: Preset file to modify
            cppython_preset_file: Path to the cppython preset file to include
            cmake_data: The CMake data to use
            build_directory: The build directory to use
        """
        initial_root_preset = None

        if preset_file.exists():
            with open(preset_file, encoding='utf-8') as file:
                initial_json = file.read()
            initial_root_preset = CMakePresets.model_validate_json(initial_json)

        root_preset = Builder.generate_root_preset(preset_file, cppython_preset_file, cmake_data, build_directory)

        # Only write the file if the data has changed
        if root_preset != initial_root_preset:
            with open(preset_file, 'w', encoding='utf-8') as file:
                preset = root_preset.model_dump_json(exclude_none=True, indent=4)
                file.write(preset)
