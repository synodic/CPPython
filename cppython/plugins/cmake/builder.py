"""Plugin builder"""

from pathlib import Path

from cppython.plugins.cmake.schema import CMakeData, CMakePresets, CMakeSyncData, ConfigurePreset


class Builder:
    """Aids in building the information needed for the CMake plugin"""

    def __init__(self) -> None:
        """Initialize the builder"""

    @staticmethod
    def generate_provider_preset(provider_data: CMakeSyncData) -> CMakePresets:
        """Generates a provider preset from input sync data

        Args:
            provider_directory: The base directory to place the preset files
            provider_data: The providers synchronization data
        """
        generated_configure_preset = ConfigurePreset(name=provider_data.provider_name, hidden=True)

        # Toss in that sync data from the provider
        generated_configure_preset.cacheVariables = {
            'CMAKE_PROJECT_TOP_LEVEL_INCLUDES': str(provider_data.top_level_includes.as_posix()),
        }

        return CMakePresets(configurePresets=[generated_configure_preset])

    @staticmethod
    def write_provider_preset(provider_directory: Path, provider_data: CMakeSyncData) -> None:
        """Writes a provider preset from input sync data

        Args:
            provider_directory: The base directory to place the preset files
            provider_data: The providers synchronization data
        """
        generated_preset = Builder.generate_provider_preset(provider_data)

        provider_preset_file = provider_directory / f'{provider_data.provider_name}.json'

        initial_preset = None

        # If the file already exists, we need to compare it
        if provider_preset_file.exists():
            with open(provider_preset_file, encoding='utf-8') as file:
                initial_json = file.read()
            initial_preset = CMakePresets.model_validate_json(initial_json)

        if generated_preset != initial_preset:
            serialized = generated_preset.model_dump_json(exclude_none=True, by_alias=False, indent=4)
            with open(provider_preset_file, 'w', encoding='utf8') as file:
                file.write(serialized)

    @staticmethod
    def generate_cppython_preset(
        cppython_preset_directory: Path, provider_directory: Path, provider_data: CMakeSyncData
    ) -> CMakePresets:
        """Generates the cppython preset which inherits from the provider presets

        Args:
            cppython_preset_directory: The tool directory
            provider_directory: The base directory containing provider presets
            provider_data: The provider's synchronization data

        Returns:
            A CMakePresets object
        """
        generated_configure_preset = ConfigurePreset(name='cppython', inherits=provider_data.provider_name, hidden=True)
        generated_preset = CMakePresets(configurePresets=[generated_configure_preset])

        # Get the relative path to the provider preset file
        provider_preset_file = provider_directory / f'{provider_data.provider_name}.json'
        relative_preset = provider_preset_file.relative_to(cppython_preset_directory, walk_up=True).as_posix()

        # Set the data
        generated_preset.include = [relative_preset]
        return generated_preset

    @staticmethod
    def write_cppython_preset(
        cppython_preset_directory: Path, provider_directory: Path, provider_data: CMakeSyncData
    ) -> Path:
        """Write the cppython presets which inherit from the provider presets

        Args:
            cppython_preset_directory: The tool directory
            provider_directory: The base directory containing provider presets
            provider_data: The provider's synchronization data

        Returns:
            A file path to the written data
        """
        generated_preset = Builder.generate_cppython_preset(
            cppython_preset_directory, provider_directory, provider_data
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
        default_configure_preset = ConfigurePreset(
            name=cmake_data.configuration_name,
            inherits='cppython',
            binaryDir=build_directory.as_posix(),
            cacheVariables={
                'CMAKE_BUILD_TYPE': 'Release'  # Ensure compatibility for single-config and multi-config generators
            },
        )

        if preset_file.exists():
            with open(preset_file, encoding='utf-8') as file:
                initial_json = file.read()
            root_preset = CMakePresets.model_validate_json(initial_json)

            if root_preset.configurePresets is None:
                root_preset.configurePresets = [default_configure_preset]

            # Set defaults
            preset = next((p for p in root_preset.configurePresets if p.name == default_configure_preset.name), None)
            if preset:
                # If the name matches, we need to verify it inherits from cppython
                if preset.inherits is None:
                    preset.inherits = 'cppython'
                elif isinstance(preset.inherits, str) and preset.inherits != 'cppython':
                    preset.inherits = [preset.inherits, 'cppython']
                elif isinstance(preset.inherits, list) and 'cppython' not in preset.inherits:
                    preset.inherits.append('cppython')
            else:
                root_preset.configurePresets.append(default_configure_preset)

        else:
            # If the file doesn't exist, we need to default it for the user
            root_preset = CMakePresets(configurePresets=[default_configure_preset])

        # Get the relative path to the cppython preset file
        preset_directory = preset_file.parent.absolute()
        relative_preset = cppython_preset_file.relative_to(preset_directory, walk_up=True).as_posix()

        # If the include key doesn't exist, we know we will write to disk afterwards
        if not root_preset.include:
            root_preset.include = []

        # Only the included preset file if it doesn't exist. Implied by the above check
        if str(relative_preset) not in root_preset.include:
            root_preset.include.append(str(relative_preset))

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
