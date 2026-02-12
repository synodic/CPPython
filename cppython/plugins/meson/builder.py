"""Plugin builder for Meson native/cross file management."""

import configparser
import io
from pathlib import Path

from cppython.plugins.meson.schema import MesonSyncData


class Builder:
    """Aids in building the information needed for the Meson plugin.

    Manages generation and writing of Meson native and cross files
    that configure dependency paths from providers.
    """

    def __init__(self) -> None:
        """Initialize the builder."""

    @staticmethod
    def generate_native_file(sync_data: MesonSyncData, project_root: Path) -> str:
        """Generates a Meson native file that references provider-managed dependencies.

        The native file points Meson to the provider's dependency paths via
        ``pkg_config_path`` and ``cmake_prefix_path`` in the ``[built-in options]``
        section. If the provider supplies its own native file, an include
        directive is used instead.

        Args:
            sync_data: The provider's synchronization data
            project_root: The project root directory

        Returns:
            The native file content as a string
        """
        config = configparser.ConfigParser()
        # Preserve key casing
        config.optionxform = str  # type: ignore[assignment]

        if sync_data.native_file:
            # Reference the provider's native file via properties
            config['properties'] = {
                'cppython_provider': f"'{sync_data.provider_name}'",
                'cppython_native_file': f"'{sync_data.native_file.as_posix()}'",
            }

        output = io.StringIO()
        config.write(output)
        return output.getvalue()

    @staticmethod
    def generate_cross_file(sync_data: MesonSyncData, project_root: Path) -> str:
        """Generates a Meson cross file that references provider-managed toolchain.

        Args:
            sync_data: The provider's synchronization data
            project_root: The project root directory

        Returns:
            The cross file content as a string
        """
        config = configparser.ConfigParser()
        config.optionxform = str  # type: ignore[assignment]

        if sync_data.cross_file:
            config['properties'] = {
                'cppython_provider': f"'{sync_data.provider_name}'",
                'cppython_cross_file': f"'{sync_data.cross_file.as_posix()}'",
            }

        output = io.StringIO()
        config.write(output)
        return output.getvalue()

    @staticmethod
    def write_native_file(directory: Path, sync_data: MesonSyncData, project_root: Path) -> Path | None:
        """Write a CPPython-managed native file to disk.

        Only writes if the provider supplied a native file. The generated file
        is written to ``{directory}/cppython_native.ini`` and is only updated
        if the content has changed.

        Args:
            directory: The tool directory to write the file to
            sync_data: The provider's synchronization data
            project_root: The project root directory

        Returns:
            Path to the written native file, or None if no native file was provided
        """
        if not sync_data.native_file:
            return None

        directory.mkdir(parents=True, exist_ok=True)
        native_file_path = directory / 'cppython_native.ini'

        content = Builder.generate_native_file(sync_data, project_root)

        # Only write if content changed
        if native_file_path.exists():
            existing = native_file_path.read_text(encoding='utf-8')
            if existing == content:
                return native_file_path

        native_file_path.write_text(content, encoding='utf-8')
        return native_file_path

    @staticmethod
    def write_cross_file(directory: Path, sync_data: MesonSyncData, project_root: Path) -> Path | None:
        """Write a CPPython-managed cross file to disk.

        Only writes if the provider supplied a cross file. The generated file
        is written to ``{directory}/cppython_cross.ini`` and is only updated
        if the content has changed.

        Args:
            directory: The tool directory to write the file to
            sync_data: The provider's synchronization data
            project_root: The project root directory

        Returns:
            Path to the written cross file, or None if no cross file was provided
        """
        if not sync_data.cross_file:
            return None

        directory.mkdir(parents=True, exist_ok=True)
        cross_file_path = directory / 'cppython_cross.ini'

        content = Builder.generate_cross_file(sync_data, project_root)

        # Only write if content changed
        if cross_file_path.exists():
            existing = cross_file_path.read_text(encoding='utf-8')
            if existing == content:
                return cross_file_path

        cross_file_path.write_text(content, encoding='utf-8')
        return cross_file_path
