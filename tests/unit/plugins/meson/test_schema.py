"""Tests for the Meson schema"""

from pathlib import Path

from cppython.plugins.meson.schema import MesonConfiguration, MesonData, MesonSyncData
from cppython.utility.utility import TypeName


class TestMesonSyncData:
    """Tests for the MesonSyncData class"""

    @staticmethod
    def test_default() -> None:
        """Tests MesonSyncData with default values."""
        data = MesonSyncData(provider_name=TypeName('test'))
        assert data.native_file is None
        assert data.cross_file is None

    @staticmethod
    def test_native_file() -> None:
        """Tests MesonSyncData with a native file."""
        data = MesonSyncData(provider_name=TypeName('conan'), native_file=Path('/path/to/native.ini'))
        assert data.native_file == Path('/path/to/native.ini')
        assert data.cross_file is None

    @staticmethod
    def test_cross_file() -> None:
        """Tests MesonSyncData with a cross file."""
        data = MesonSyncData(provider_name=TypeName('conan'), cross_file=Path('/path/to/cross.ini'))
        assert data.native_file is None
        assert data.cross_file == Path('/path/to/cross.ini')

    @staticmethod
    def test_both_files() -> None:
        """Tests MesonSyncData with both native and cross files."""
        data = MesonSyncData(
            provider_name=TypeName('conan'),
            native_file=Path('/path/to/native.ini'),
            cross_file=Path('/path/to/cross.ini'),
        )
        assert data.native_file == Path('/path/to/native.ini')
        assert data.cross_file == Path('/path/to/cross.ini')


class TestMesonConfiguration:
    """Tests for the MesonConfiguration class"""

    @staticmethod
    def test_defaults() -> None:
        """Tests MesonConfiguration with default values."""
        config = MesonConfiguration()
        assert config.build_file == Path('meson.build')
        assert config.build_directory == 'builddir'
        assert config.meson_binary is None

    @staticmethod
    def test_custom_values() -> None:
        """Tests MesonConfiguration with custom values."""
        config = MesonConfiguration(
            build_file=Path('subdir/meson.build'),
            build_directory='custom-build',
            meson_binary=Path('/usr/bin/meson'),
        )
        assert config.build_file == Path('subdir/meson.build')
        assert config.build_directory == 'custom-build'
        assert config.meson_binary == Path('/usr/bin/meson')


class TestMesonData:
    """Tests for the MesonData class"""

    @staticmethod
    def test_construction() -> None:
        """Tests MesonData construction."""
        data = MesonData(
            build_file=Path('/project/meson.build'),
            build_directory='builddir',
            meson_binary=None,
        )
        assert data.build_file == Path('/project/meson.build')
        assert data.build_directory == 'builddir'
        assert data.meson_binary is None
