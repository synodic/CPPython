"""Tests for CMakePresets"""

from pathlib import Path

from cppython.plugins.cmake.builder import Builder
from cppython.plugins.cmake.schema import CMakePresets, CMakeSyncData
from cppython.utility.utility import TypeName


class TestCMakePresets:
    """Tests for the CMakePresets class"""

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
    def test_root_write(tmp_path: Path) -> None:
        """Verifies that the root preset writing works as intended

        Args:
            tmp_path: The input path the use
        """
        builder = Builder()

        cppython_preset_directory = tmp_path / 'cppython'
        cppython_preset_directory.mkdir(parents=True, exist_ok=True)

        provider_directory = cppython_preset_directory / 'providers'
        provider_directory.mkdir(parents=True, exist_ok=True)

        includes_file = provider_directory / 'includes.cmake'
        with includes_file.open('w', encoding='utf-8') as file:
            file.write('example contents')

        root_file = tmp_path / 'CMakePresets.json'
        presets = CMakePresets()

        serialized = presets.model_dump_json(exclude_none=True, by_alias=False, indent=4)
        with open(root_file, 'w', encoding='utf8') as file:
            file.write(serialized)

        data = CMakeSyncData(provider_name=TypeName('test-provider'), top_level_includes=includes_file)
        builder.write_provider_preset(provider_directory, data)

        cppython_preset_file = builder.write_cppython_preset(cppython_preset_directory, provider_directory, data)

        builder.write_root_presets(root_file, cppython_preset_file)

    @staticmethod
    def test_relative_root_write(tmp_path: Path) -> None:
        """Verifies that the root preset writing works as intended

        Args:
            tmp_path: The input path the use
        """
        builder = Builder()

        cppython_preset_directory = tmp_path / 'tool' / 'cppython'
        cppython_preset_directory.mkdir(parents=True, exist_ok=True)

        provider_directory = cppython_preset_directory / 'providers'
        provider_directory.mkdir(parents=True, exist_ok=True)

        includes_file = provider_directory / 'includes.cmake'
        with includes_file.open('w', encoding='utf-8') as file:
            file.write('example contents')

        relative_indirection = tmp_path / 'nested'
        relative_indirection.mkdir(parents=True, exist_ok=True)

        root_file = relative_indirection / 'CMakePresets.json'
        presets = CMakePresets()
        serialized = presets.model_dump_json(exclude_none=True, by_alias=False, indent=4)
        with open(root_file, 'w', encoding='utf8') as file:
            file.write(serialized)

        data = CMakeSyncData(provider_name=TypeName('test-provider'), top_level_includes=includes_file)
        builder.write_provider_preset(provider_directory, data)

        cppython_preset_file = builder.write_cppython_preset(cppython_preset_directory, provider_directory, data)
        builder.write_root_presets(root_file, cppython_preset_file)
