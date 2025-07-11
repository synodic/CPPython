"""Tests for CMakePresets"""

from pathlib import Path

from cppython.core.schema import ProjectData
from cppython.plugins.cmake.builder import Builder
from cppython.plugins.cmake.schema import CMakeData, CMakePresets, CMakeSyncData
from cppython.utility.utility import TypeName


class TestBuilder:
    """Tests for the CMakePresets class"""

    @staticmethod
    def test_generate_root_preset_new(project_data: ProjectData) -> None:
        """Test generate_root_preset when the preset file does not exist"""
        builder = Builder()
        preset_file = project_data.project_root / 'CMakePresets.json'
        cppython_preset_file = project_data.project_root / 'cppython.json'
        cmake_data = CMakeData(preset_file=preset_file, configuration_name='test-configuration')

        build_directory = project_data.project_root / 'build'

        # The function should create a new preset with the correct name and inheritance
        result = builder.generate_root_preset(preset_file, cppython_preset_file, cmake_data, build_directory)
        assert result.configurePresets is not None
        assert any(p.name == 'test-configuration' for p in result.configurePresets)

        preset = next(p for p in result.configurePresets if p.name == 'test-configuration')
        assert preset.inherits == 'cppython'

    @staticmethod
    def test_generate_root_preset_existing(project_data: ProjectData) -> None:
        """Test generate_root_preset when the preset file already exists"""
        builder = Builder()
        preset_file = project_data.project_root / 'CMakePresets.json'
        cppython_preset_file = project_data.project_root / 'cppython.json'
        cmake_data = CMakeData(preset_file=preset_file, configuration_name='test-configuration')

        # Create an initial preset file with a different preset
        initial_presets = CMakePresets(configurePresets=[])
        with open(preset_file, 'w', encoding='utf-8') as f:
            f.write(initial_presets.model_dump_json(exclude_none=True, by_alias=False, indent=4))

        build_directory = project_data.project_root / 'build'

        # Should add the new preset and include
        result = builder.generate_root_preset(preset_file, cppython_preset_file, cmake_data, build_directory)
        assert result.configurePresets is not None
        assert any(p.name == 'test-configuration' for p in result.configurePresets)


class TestWrites:
    """Tests for writing the CMakePresets class"""

    @staticmethod
    def test_provider_write(tmp_path: Path) -> None:
        """Verifies that the provider preset writing works as intended

        Args:
            tmp_path: The input path the use
        """
        builder = Builder()

        includes_file = tmp_path / 'includes.cmake'
        with includes_file.open('w', encoding='utf-8') as file:
            file.write('example contents')

        data = CMakeSyncData(provider_name=TypeName('test-provider'), top_level_includes=includes_file)
        builder.write_provider_preset(tmp_path, data)

    @staticmethod
    def test_cppython_write(tmp_path: Path) -> None:
        """Verifies that the cppython preset writing works as intended

        Args:
            tmp_path: The input path the use
        """
        builder = Builder()

        provider_directory = tmp_path / 'providers'
        provider_directory.mkdir(parents=True, exist_ok=True)

        includes_file = provider_directory / 'includes.cmake'
        with includes_file.open('w', encoding='utf-8') as file:
            file.write('example contents')

        data = CMakeSyncData(provider_name=TypeName('test-provider'), top_level_includes=includes_file)
        builder.write_provider_preset(provider_directory, data)

        builder.write_cppython_preset(tmp_path, provider_directory, data)

    @staticmethod
    def test_root_write(project_data: ProjectData) -> None:
        """Verifies that the root preset writing works as intended

        Args:
            project_data: The project data with a temporary workspace
        """
        builder = Builder()

        cppython_preset_directory = project_data.project_root / 'cppython'
        cppython_preset_directory.mkdir(parents=True, exist_ok=True)

        provider_directory = cppython_preset_directory / 'providers'
        provider_directory.mkdir(parents=True, exist_ok=True)

        includes_file = provider_directory / 'includes.cmake'
        with includes_file.open('w', encoding='utf-8') as file:
            file.write('example contents')

        root_file = project_data.project_root / 'CMakePresets.json'
        presets = CMakePresets()

        serialized = presets.model_dump_json(exclude_none=True, by_alias=False, indent=4)
        with open(root_file, 'w', encoding='utf8') as file:
            file.write(serialized)

        data = CMakeSyncData(provider_name=TypeName('test-provider'), top_level_includes=includes_file)
        builder.write_provider_preset(provider_directory, data)

        cppython_preset_file = builder.write_cppython_preset(cppython_preset_directory, provider_directory, data)

        build_directory = project_data.project_root / 'build'
        builder.write_root_presets(
            root_file,
            cppython_preset_file,
            CMakeData(preset_file=root_file, configuration_name='default'),
            build_directory,
        )

    @staticmethod
    def test_relative_root_write(project_data: ProjectData) -> None:
        """Verifies that the root preset writing works as intended

        Args:
            project_data: The project data with a temporary workspace
        """
        builder = Builder()

        cppython_preset_directory = project_data.project_root / 'tool' / 'cppython'
        cppython_preset_directory.mkdir(parents=True, exist_ok=True)

        provider_directory = cppython_preset_directory / 'providers'
        provider_directory.mkdir(parents=True, exist_ok=True)

        includes_file = provider_directory / 'includes.cmake'
        with includes_file.open('w', encoding='utf-8') as file:
            file.write('example contents')

        relative_indirection = project_data.project_root / 'nested'
        relative_indirection.mkdir(parents=True, exist_ok=True)

        root_file = relative_indirection / 'CMakePresets.json'
        presets = CMakePresets()
        serialized = presets.model_dump_json(exclude_none=True, by_alias=False, indent=4)
        with open(root_file, 'w', encoding='utf8') as file:
            file.write(serialized)

        data = CMakeSyncData(provider_name=TypeName('test-provider'), top_level_includes=includes_file)
        builder.write_provider_preset(provider_directory, data)

        cppython_preset_file = builder.write_cppython_preset(cppython_preset_directory, provider_directory, data)

        build_directory = project_data.project_root / 'build'
        builder.write_root_presets(
            root_file,
            cppython_preset_file,
            CMakeData(preset_file=root_file, configuration_name='default'),
            build_directory,
        )
