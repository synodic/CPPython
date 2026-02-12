"""Tests the Project type"""

import logging
import tomllib
from importlib import metadata
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from cppython.core.schema import (
    CPPythonLocalConfiguration,
    PEP621Configuration,
    ProjectConfiguration,
    PyProject,
    ToolData,
)
from cppython.project import Project
from cppython.test.mock.generator import MockGenerator
from cppython.test.mock.interface import MockInterface
from cppython.test.mock.provider import MockProvider
from cppython.test.mock.scm import MockSCM
from cppython.utility.exception import InstallationVerificationError

pep621 = PEP621Configuration(name='test-project', version='0.1.0')


class TestProject:
    """Various tests for the project object"""

    @staticmethod
    def test_self_construction(request: pytest.FixtureRequest) -> None:
        """The project type should be constructable with this projects configuration

        Args:
            request: The pytest request fixture
        """
        # Use the CPPython directory as the test data
        file = request.config.rootpath / 'pyproject.toml'
        project_configuration = ProjectConfiguration(project_root=file.parent, version=None)
        interface = MockInterface()

        pyproject_data = tomllib.loads(file.read_text(encoding='utf-8'))
        project = Project(project_configuration, interface, pyproject_data)

        # Doesn't have the cppython table
        assert not project.enabled

    @staticmethod
    def test_missing_tool_table(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        """The project type should be constructable without the tool table

        Args:
            tmp_path: Temporary directory for dummy data
            caplog: Pytest fixture for capturing logs
        """
        file_path = tmp_path / 'pyproject.toml'

        with open(file_path, 'a', encoding='utf8'):
            pass

        project_configuration = ProjectConfiguration(project_root=file_path.parent, version=None)
        interface = MockInterface()

        pyproject = PyProject(project=pep621)

        with caplog.at_level(logging.WARNING):
            project = Project(project_configuration, interface, pyproject.model_dump(by_alias=True))

        # We don't want to have the log of the calling tool polluted with any default logging
        assert len(caplog.records) == 0

        assert not project.enabled

    @staticmethod
    def test_missing_cppython_table(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        """The project type should be constructable without the cppython table

        Args:
            tmp_path: Temporary directory for dummy data
            caplog: Pytest fixture for capturing logs
        """
        file_path = tmp_path / 'pyproject.toml'

        with open(file_path, 'a', encoding='utf8'):
            pass

        project_configuration = ProjectConfiguration(project_root=file_path.parent, version=None)
        interface = MockInterface()

        tool_data = ToolData()
        pyproject = PyProject(project=pep621, tool=tool_data)

        with caplog.at_level(logging.WARNING):
            project = Project(project_configuration, interface, pyproject.model_dump(by_alias=True))

        # We don't want to have the log of the calling tool polluted with any default logging
        assert len(caplog.records) == 0

        assert not project.enabled

    @staticmethod
    def test_default_cppython_table(tmp_path: Path, mocker: MockerFixture, caplog: pytest.LogCaptureFixture) -> None:
        """The project type should be constructable with the default cppython table

        Args:
            tmp_path: Temporary directory for dummy data
            mocker: Pytest mocker fixture
            caplog: Pytest fixture for capturing logs
        """
        # Insert ourself into the builder and load the mock plugins by returning them directly in the expected order
        #   they will be built
        mocker.patch(
            'cppython.builder.entry_points',
            return_value=[metadata.EntryPoint(name='mock', value='mock', group='mock')],
        )
        mocker.patch.object(metadata.EntryPoint, 'load', side_effect=[MockGenerator, MockProvider, MockSCM])

        file_path = tmp_path / 'pyproject.toml'

        with open(file_path, 'a', encoding='utf8'):
            pass

        project_configuration = ProjectConfiguration(project_root=file_path.parent, version=None)
        interface = MockInterface()

        cppython_config = CPPythonLocalConfiguration()
        tool_data = ToolData(cppython=cppython_config)
        pyproject = PyProject(project=pep621, tool=tool_data)

        with caplog.at_level(logging.WARNING):
            project = Project(project_configuration, interface, pyproject.model_dump(by_alias=True))

        # We don't want to have the log of the calling tool polluted with any default logging
        assert len(caplog.records) == 0

        assert project.enabled


class TestPrepareBuild:
    """Tests for Project.prepare_build()"""

    @staticmethod
    def _create_enabled_project(tmp_path: Path, mocker: MockerFixture) -> Project:
        """Helper to create an enabled project with mock plugins.

        Args:
            tmp_path: Temporary directory
            mocker: Pytest mocker fixture

        Returns:
            An enabled Project instance
        """
        mocker.patch(
            'cppython.builder.entry_points',
            return_value=[metadata.EntryPoint(name='mock', value='mock', group='mock')],
        )
        mocker.patch.object(metadata.EntryPoint, 'load', side_effect=[MockGenerator, MockProvider, MockSCM])

        file_path = tmp_path / 'pyproject.toml'
        with open(file_path, 'a', encoding='utf8'):
            pass

        project_configuration = ProjectConfiguration(project_root=file_path.parent, version=None)
        interface = MockInterface()

        cppython_config = CPPythonLocalConfiguration()
        tool_data = ToolData(cppython=cppython_config)
        pyproject = PyProject(project=pep621, tool=tool_data)

        return Project(project_configuration, interface, pyproject.model_dump(by_alias=True))

    def test_prepare_build_calls_sync_and_verify(self, tmp_path: Path, mocker: MockerFixture) -> None:
        """prepare_build() should call sync and verify_installed, not install.

        Args:
            tmp_path: Temporary directory
            mocker: Pytest mocker fixture
        """
        project = self._create_enabled_project(tmp_path, mocker)
        assert project.enabled

        # Spy on the key methods
        sync_spy = mocker.patch.object(project._data, 'sync')  # noqa: SLF001
        verify_spy = mocker.patch.object(project._data.plugins.provider, 'verify_installed')  # noqa: SLF001
        install_spy = mocker.patch.object(project._data.plugins.provider, 'install')  # noqa: SLF001

        project.prepare_build()

        sync_spy.assert_called_once()
        verify_spy.assert_called_once()
        install_spy.assert_not_called()

    def test_prepare_build_returns_none_when_disabled(self, tmp_path: Path) -> None:
        """prepare_build() should return None for a disabled project.

        Args:
            tmp_path: Temporary directory
        """
        file_path = tmp_path / 'pyproject.toml'
        with open(file_path, 'a', encoding='utf8'):
            pass

        project_configuration = ProjectConfiguration(project_root=file_path.parent, version=None)
        interface = MockInterface()

        pyproject = PyProject(project=pep621)
        project = Project(project_configuration, interface, pyproject.model_dump(by_alias=True))

        assert not project.enabled
        assert project.prepare_build() is None

    def test_prepare_build_raises_on_missing_artifacts(self, tmp_path: Path, mocker: MockerFixture) -> None:
        """prepare_build() should propagate InstallationVerificationError.

        Args:
            tmp_path: Temporary directory
            mocker: Pytest mocker fixture
        """
        project = self._create_enabled_project(tmp_path, mocker)
        assert project.enabled

        # Make verify_installed raise
        mocker.patch.object(project._data, 'sync')  # noqa: SLF001
        mocker.patch.object(
            project._data.plugins.provider,  # noqa: SLF001
            'verify_installed',
            side_effect=InstallationVerificationError('mock', ['test artifact']),
        )

        with pytest.raises(InstallationVerificationError, match='mock'):
            project.prepare_build()
