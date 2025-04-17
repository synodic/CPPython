"""Tests the scope of utilities"""

import logging
from logging import StreamHandler
from pathlib import Path
from typing import NamedTuple

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
