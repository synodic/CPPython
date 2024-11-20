"""Unit test the provider plugin"""

from pathlib import Path
from typing import Any

import pytest

from cppython.core.utility import write_model_json
from cppython.plugins.cmake.builder import Builder
from cppython.plugins.cmake.plugin import CMakeGenerator
from cppython.plugins.cmake.schema import (
    CMakeConfiguration,
    CMakePresets,
    CMakeSyncData,
)
from cppython.test.pytest.tests import GeneratorUnitTests
from cppython.utility.utility import TypeName


class TestCPPythonGenerator(GeneratorUnitTests[CMakeGenerator]):
    """The tests for the CMake generator"""

    @staticmethod
    @pytest.fixture(name='plugin_data', scope='session')
    def fixture_plugin_data(cmake_data: CMakeConfiguration) -> dict[str, Any]:
        """A required testing hook that allows data generation

        Args:
            cmake_data: The input data

        Returns:
            The constructed plugin data
        """
        return cmake_data.model_dump()

    @staticmethod
    @pytest.fixture(name='plugin_type', scope='session')
    def fixture_plugin_type() -> type[CMakeGenerator]:
        """A required testing hook that allows type generation

        Returns:
            The type of the Generator
        """
        return CMakeGenerator

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
        write_model_json(root_file, presets)

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
        write_model_json(root_file, presets)

        data = CMakeSyncData(provider_name=TypeName('test-provider'), top_level_includes=includes_file)
        builder.write_provider_preset(provider_directory, data)

        cppython_preset_file = builder.write_cppython_preset(cppython_preset_directory, provider_directory, data)
        builder.write_root_presets(root_file, cppython_preset_file)
