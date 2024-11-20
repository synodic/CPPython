"""Tests the scope of utilities"""

import logging
from logging import StreamHandler
from pathlib import Path
from sys import executable
from typing import NamedTuple

import pytest

from cppython.utility.exception import ProcessError
from cppython.utility.subprocess import call
from cppython.utility.utility import canonicalize_name

cppython_logger = logging.getLogger('cppython')
cppython_logger.addHandler(StreamHandler())


class TestUtility:
    """Tests the utility functionality"""

    class ModelTest(NamedTuple):
        """Model definition to help test IO utilities"""

        test_path: Path
        test_int: int

    @staticmethod
    def test_none() -> None:
        """Verifies that no exception is thrown with an empty string"""
        test = canonicalize_name('')

        assert not test.group
        assert not test.name

    @staticmethod
    def test_only_group() -> None:
        """Verifies that no exception is thrown when only a group is specified"""
        test = canonicalize_name('Group')

        assert test.group == 'group'
        assert not test.name

    @staticmethod
    def test_name_group() -> None:
        """Test that canonicalization works"""
        test = canonicalize_name('NameGroup')

        assert test.group == 'group'
        assert test.name == 'name'

    @staticmethod
    def test_group_only_caps() -> None:
        """Test that canonicalization works"""
        test = canonicalize_name('NameGROUP')

        assert test.group == 'group'
        assert test.name == 'name'

    @staticmethod
    def test_name_only_caps() -> None:
        """Test that canonicalization works"""
        test = canonicalize_name('NAMEGroup')
        assert test.group == 'group'
        assert test.name == 'name'

    @staticmethod
    def test_name_multi_caps() -> None:
        """Test that caps works"""
        test = canonicalize_name('NAmeGroup')
        assert test.group == 'group'
        assert test.name == 'name'


class TestSubprocess:
    """Subprocess testing"""

    @staticmethod
    def test_subprocess_stdout(caplog: pytest.LogCaptureFixture) -> None:
        """Test subprocess_call

        Args:
            caplog: Fixture for capturing logging input
        """
        python = Path(executable)

        with caplog.at_level(logging.INFO):
            call(
                [python, '-c', "import sys; print('Test Out', file = sys.stdout)"],
                cppython_logger,
            )

        assert len(caplog.records) == 1
        assert caplog.records[0].message == 'Test Out'

    @staticmethod
    def test_subprocess_stderr(caplog: pytest.LogCaptureFixture) -> None:
        """Test subprocess_call

        Args:
            caplog: Fixture for capturing logging input
        """
        python = Path(executable)

        with caplog.at_level(logging.INFO):
            call(
                [python, '-c', "import sys; print('Test Error', file = sys.stderr)"],
                cppython_logger,
            )

        assert len(caplog.records) == 1
        assert caplog.records[0].message == 'Test Error'

    @staticmethod
    def test_subprocess_suppression(caplog: pytest.LogCaptureFixture) -> None:
        """Test subprocess_call suppression flag

        Args:
            caplog: Fixture for capturing logging input
        """
        python = Path(executable)

        with caplog.at_level(logging.INFO):
            call(
                [python, '-c', "import sys; print('Test Out', file = sys.stdout)"],
                cppython_logger,
                suppress=True,
            )
            assert len(caplog.records) == 0

    @staticmethod
    def test_subprocess_exit(caplog: pytest.LogCaptureFixture) -> None:
        """Test subprocess_call exception output

        Args:
            caplog: Fixture for capturing logging input
        """
        python = Path(executable)

        with pytest.raises(ProcessError) as exec_info, caplog.at_level(logging.INFO):
            call(
                [python, '-c', "import sys; sys.exit('Test Exit Output')"],
                cppython_logger,
            )

        assert len(caplog.records) == 1
        assert caplog.records[0].message == 'Test Exit Output'

        assert 'Subprocess task failed' in str(exec_info.value)

    @staticmethod
    def test_subprocess_exception(caplog: pytest.LogCaptureFixture) -> None:
        """Test subprocess_call exception output

        Args:
            caplog: Fixture for capturing logging input
        """
        python = Path(executable)

        with pytest.raises(ProcessError) as exec_info, caplog.at_level(logging.INFO):
            call(
                [python, '-c', "import sys; raise Exception('Test Exception Output')"],
                cppython_logger,
            )
        assert len(caplog.records) == 1
        assert caplog.records[0].message == 'Test Exception Output'

        assert 'Subprocess task failed' in str(exec_info.value)

    @staticmethod
    def test_stderr_exception(caplog: pytest.LogCaptureFixture) -> None:
        """Verify print and exit

        Args:
            caplog: Fixture for capturing logging input
        """
        python = Path(executable)
        with pytest.raises(ProcessError) as exec_info, caplog.at_level(logging.INFO):
            call(
                [
                    python,
                    '-c',
                    "import sys; print('Test Out', file = sys.stdout); sys.exit('Test Exit Out')",
                ],
                cppython_logger,
            )

        LOG_COUNT = 2
        assert len(caplog.records) == LOG_COUNT
        assert caplog.records[0].message == 'Test Out'
        assert caplog.records[1].message == 'Test Exit Out'

        assert 'Subprocess task failed' in str(exec_info.value)

    @staticmethod
    def test_stdout_exception(caplog: pytest.LogCaptureFixture) -> None:
        """Verify print and exit

        Args:
            caplog: Fixture for capturing logging input
        """
        python = Path(executable)
        with pytest.raises(ProcessError) as exec_info, caplog.at_level(logging.INFO):
            call(
                [
                    python,
                    '-c',
                    "import sys; print('Test Error', file = sys.stderr); sys.exit('Test Exit Error')",
                ],
                cppython_logger,
            )

        LOG_COUNT = 2
        assert len(caplog.records) == LOG_COUNT
        assert caplog.records[0].message == 'Test Error'
        assert caplog.records[1].message == 'Test Exit Error'

        assert 'Subprocess task failed' in str(exec_info.value)
