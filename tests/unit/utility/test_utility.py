"""Tests the scope of utilities"""

import logging
from logging import StreamHandler
from pathlib import Path
from sys import executable
from typing import NamedTuple

import pytest
from pytest import LogCaptureFixture

from synodic_utilities.exception import ProcessError
from synodic_utilities.subprocess import call
from synodic_utilities.utility import canonicalize_name

cppython_logger = logging.getLogger("cppython")
cppython_logger.addHandler(StreamHandler())


class TestUtility:
    """Tests the utility functionality"""

    class ModelTest(NamedTuple):
        """Model definition to help test IO utilities"""

        test_path: Path
        test_int: int

    def test_none(self) -> None:
        """Verifies that no exception is thrown with an empty string"""

        test = canonicalize_name("")

        assert test.group == ""
        assert test.name == ""

    def test_only_group(self) -> None:
        """Verifies that no exception is thrown when only a group is specified"""

        test = canonicalize_name("Group")

        assert test.group == "group"
        assert test.name == ""

    def test_name_group(self) -> None:
        """Test that canonicalization works"""

        test = canonicalize_name("NameGroup")

        assert test.group == "group"
        assert test.name == "name"

    def test_group_only_caps(self) -> None:
        """Test that canonicalization works"""
        test = canonicalize_name("NameGROUP")

        assert test.group == "group"
        assert test.name == "name"

    def test_name_only_caps(self) -> None:
        """Test that canonicalization works"""
        test = canonicalize_name("NAMEGroup")
        assert test.group == "group"
        assert test.name == "name"

    def test_name_multi_caps(self) -> None:
        """Test that caps works"""
        test = canonicalize_name("NAmeGroup")
        assert test.group == "group"
        assert test.name == "name"


class TestSubprocess:
    """Subprocess testing"""

    def test_subprocess_stdout(self, caplog: LogCaptureFixture) -> None:
        """Test subprocess_call

        Args:
            caplog: Fixture for capturing logging input
        """

        python = Path(executable)

        with caplog.at_level(logging.INFO):
            call(
                [python, "-c", "import sys; print('Test Out', file = sys.stdout)"],
                cppython_logger,
            )

        assert len(caplog.records) == 1
        assert "Test Out" == caplog.records[0].message

    def test_subprocess_stderr(self, caplog: LogCaptureFixture) -> None:
        """Test subprocess_call

        Args:
            caplog: Fixture for capturing logging input
        """

        python = Path(executable)

        with caplog.at_level(logging.INFO):
            call(
                [python, "-c", "import sys; print('Test Error', file = sys.stderr)"],
                cppython_logger,
            )

        assert len(caplog.records) == 1
        assert "Test Error" == caplog.records[0].message

    def test_subprocess_suppression(self, caplog: LogCaptureFixture) -> None:
        """Test subprocess_call suppression flag

        Args:
            caplog: Fixture for capturing logging input
        """

        python = Path(executable)

        with caplog.at_level(logging.INFO):
            call(
                [python, "-c", "import sys; print('Test Out', file = sys.stdout)"],
                cppython_logger,
                suppress=True,
            )
            assert len(caplog.records) == 0

    def test_subprocess_exit(self, caplog: LogCaptureFixture) -> None:
        """Test subprocess_call exception output

        Args:
            caplog: Fixture for capturing logging input
        """

        python = Path(executable)

        with pytest.raises(ProcessError) as exec_info, caplog.at_level(logging.INFO):
            call(
                [python, "-c", "import sys; sys.exit('Test Exit Output')"],
                cppython_logger,
            )

            assert len(caplog.records) == 1
            assert "Test Exit Output" == caplog.records[0].message

        assert "Subprocess task failed" in str(exec_info.value)

    def test_subprocess_exception(self, caplog: LogCaptureFixture) -> None:
        """Test subprocess_call exception output

        Args:
            caplog: Fixture for capturing logging input
        """

        python = Path(executable)

        with pytest.raises(ProcessError) as exec_info, caplog.at_level(logging.INFO):
            call(
                [python, "-c", "import sys; raise Exception('Test Exception Output')"],
                cppython_logger,
            )
            assert len(caplog.records) == 1
            assert "Test Exception Output" == caplog.records[0].message

        assert "Subprocess task failed" in str(exec_info.value)

    def test_stderr_exception(self, caplog: LogCaptureFixture) -> None:
        """Verify print and exit

        Args:
            caplog: Fixture for capturing logging input
        """
        python = Path(executable)
        with pytest.raises(ProcessError) as exec_info, caplog.at_level(logging.INFO):
            call(
                [
                    python,
                    "-c",
                    "import sys; print('Test Out', file = sys.stdout); sys.exit('Test Exit Out')",
                ],
                cppython_logger,
            )
            assert len(caplog.records) == 2
            assert "Test Out" == caplog.records[0].message
            assert "Test Exit Out" == caplog.records[1].message

        assert "Subprocess task failed" in str(exec_info.value)

    def test_stdout_exception(self, caplog: LogCaptureFixture) -> None:
        """Verify print and exit

        Args:
            caplog: Fixture for capturing logging input
        """
        python = Path(executable)
        with pytest.raises(ProcessError) as exec_info, caplog.at_level(logging.INFO):
            call(
                [
                    python,
                    "-c",
                    "import sys; print('Test Error', file = sys.stderr); sys.exit('Test Exit Error')",
                ],
                cppython_logger,
            )
            assert len(caplog.records) == 2
            assert "Test Error" == caplog.records[0].message
            assert "Test Exit Error" == caplog.records[1].message

        assert "Subprocess task failed" in str(exec_info.value)
