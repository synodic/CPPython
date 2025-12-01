"""Unit tests for Conan builder functionality."""

from pathlib import Path
from textwrap import dedent

import pytest

from cppython.plugins.conan.builder import Builder
from cppython.plugins.conan.schema import ConanDependency, ConanfileGenerationData, ConanVersion


class TestBuilder:
    """Test the Conan Builder class."""

    @pytest.fixture
    def builder(self) -> Builder:
        """Create a Builder instance for testing."""
        return Builder()

    def test_mixed_dependencies(self, builder: Builder, tmp_path: Path) -> None:
        """Test base conanfile with both regular and test dependencies."""
        base_file = tmp_path / 'conanfile_base.py'

        dependencies = [
            ConanDependency(name='boost', version=ConanVersion.from_string('1.80.0')),
        ]
        dependency_groups = {
            'test': [
                ConanDependency(name='gtest', version=ConanVersion.from_string('1.14.0')),
            ]
        }

        builder._create_base_conanfile(base_file, dependencies, dependency_groups)

        assert base_file.exists()
        content = base_file.read_text(encoding='utf-8')
        assert 'self.requires("boost/1.80.0")' in content
        assert 'self.test_requires("gtest/1.14.0")' in content

    def test_creates_both_files(self, builder: Builder, tmp_path: Path) -> None:
        """Test generate_conanfile creates both base and user files."""
        dependencies = [
            ConanDependency(name='boost', version=ConanVersion.from_string('1.80.0')),
        ]
        dependency_groups = {}

        data = ConanfileGenerationData(
            dependencies=dependencies,
            dependency_groups=dependency_groups,
            name='test-project',
            version='1.0.0',
        )
        builder.generate_conanfile(
            directory=tmp_path,
            data=data,
        )

        base_file = tmp_path / 'conanfile_base.py'
        conan_file = tmp_path / 'conanfile.py'

        assert base_file.exists()
        assert conan_file.exists()

    def test_regenerates_base_file(self, builder: Builder, tmp_path: Path) -> None:
        """Test base file is always regenerated with new dependencies."""
        initial_dependencies = [
            ConanDependency(name='boost', version=ConanVersion.from_string('1.80.0')),
        ]

        initial_data = ConanfileGenerationData(
            dependencies=initial_dependencies,
            dependency_groups={},
            name='test-project',
            version='1.0.0',
        )
        builder.generate_conanfile(
            directory=tmp_path,
            data=initial_data,
        )

        base_file = tmp_path / 'conanfile_base.py'
        initial_content = base_file.read_text(encoding='utf-8')
        assert 'boost/1.80.0' in initial_content

        updated_dependencies = [
            ConanDependency(name='zlib', version=ConanVersion.from_string('1.2.13')),
        ]

        updated_data = ConanfileGenerationData(
            dependencies=updated_dependencies,
            dependency_groups={},
            name='test-project',
            version='1.0.0',
        )
        builder.generate_conanfile(
            directory=tmp_path,
            data=updated_data,
        )

        updated_content = base_file.read_text(encoding='utf-8')
        assert 'zlib/1.2.13' in updated_content
        assert 'boost/1.80.0' not in updated_content

    def test_preserves_user_file(self, builder: Builder, tmp_path: Path) -> None:
        """Test user conanfile is never modified once created."""
        conan_file = tmp_path / 'conanfile.py'
        custom_content = dedent("""
            from conanfile_base import CPPythonBase
            
            class CustomPackage(CPPythonBase):
                name = "custom"
                version = "1.0.0"
                
                def requirements(self):
                    super().requirements()
                    self.requires("custom-lib/1.0.0")
        """)
        conan_file.write_text(custom_content)

        dependencies = [
            ConanDependency(name='boost', version=ConanVersion.from_string('1.80.0')),
        ]

        data = ConanfileGenerationData(
            dependencies=dependencies,
            dependency_groups={},
            name='new-name',
            version='2.0.0',
        )
        builder.generate_conanfile(
            directory=tmp_path,
            data=data,
        )

        final_content = conan_file.read_text()
        assert final_content == custom_content
        assert 'CustomPackage' in final_content
        assert 'custom-lib/1.0.0' in final_content

    def test_inheritance_chain(self, builder: Builder, tmp_path: Path) -> None:
        """Test complete inheritance chain from base to user file."""
        dependencies = [
            ConanDependency(name='boost', version=ConanVersion.from_string('1.80.0')),
            ConanDependency(name='zlib', version=ConanVersion.from_string('1.2.13')),
        ]
        dependency_groups = {
            'test': [
                ConanDependency(name='gtest', version=ConanVersion.from_string('1.14.0')),
            ]
        }

        data = ConanfileGenerationData(
            dependencies=dependencies,
            dependency_groups=dependency_groups,
            name='test-project',
            version='1.0.0',
        )
        builder.generate_conanfile(
            directory=tmp_path,
            data=data,
        )

        base_content = (tmp_path / 'conanfile_base.py').read_text(encoding='utf-8')
        user_content = (tmp_path / 'conanfile.py').read_text(encoding='utf-8')

        assert 'self.requires("boost/1.80.0")' in base_content
        assert 'self.requires("zlib/1.2.13")' in base_content
        assert 'self.test_requires("gtest/1.14.0")' in base_content

        assert 'from conanfile_base import CPPythonBase' in user_content
        assert 'class TestProjectPackage(CPPythonBase):' in user_content
        assert 'super().requirements()' in user_content
        assert 'super().build_requirements()' in user_content
