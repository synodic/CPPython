"""Tests the typer interface type"""

import pytest
import typer
from typer.testing import CliRunner

from cppython.console.entry import _parse_groups_argument, app

runner = CliRunner()


class TestConsole:
    """Various that all the examples are accessible to cppython. The project should be mocked so nothing executes"""

    @staticmethod
    def test_entrypoint() -> None:
        """Verifies that the entry functions with CPPython hooks"""
        with runner.isolated_filesystem():
            runner.invoke(app, [])


class TestParseGroupsArgument:
    """Tests for the _parse_groups_argument helper function"""

    @staticmethod
    def test_none_input() -> None:
        """Test that None input returns None"""
        assert _parse_groups_argument(None) is None

    @staticmethod
    def test_empty_string() -> None:
        """Test that empty string returns None"""
        assert _parse_groups_argument('') is None
        assert _parse_groups_argument('   ') is None

    @staticmethod
    def test_single_group() -> None:
        """Test parsing a single group"""
        result = _parse_groups_argument('[test]')
        assert result == ['test']

    @staticmethod
    def test_multiple_groups() -> None:
        """Test parsing multiple groups"""
        result = _parse_groups_argument('[dev,test]')
        assert result == ['dev', 'test']

    @staticmethod
    def test_groups_with_spaces() -> None:
        """Test parsing groups with whitespace"""
        result = _parse_groups_argument('[dev, test, docs]')
        assert result == ['dev', 'test', 'docs']

    @staticmethod
    def test_missing_brackets() -> None:
        """Test that missing brackets raises an error"""
        with pytest.raises(typer.BadParameter, match='Invalid groups format'):
            _parse_groups_argument('test')

    @staticmethod
    def test_missing_opening_bracket() -> None:
        """Test that missing opening bracket raises an error"""
        with pytest.raises(typer.BadParameter, match='Invalid groups format'):
            _parse_groups_argument('test]')

    @staticmethod
    def test_missing_closing_bracket() -> None:
        """Test that missing closing bracket raises an error"""
        with pytest.raises(typer.BadParameter, match='Invalid groups format'):
            _parse_groups_argument('[test')

    @staticmethod
    def test_empty_brackets() -> None:
        """Test that empty brackets raises an error"""
        with pytest.raises(typer.BadParameter, match='Empty groups specification'):
            _parse_groups_argument('[]')

    @staticmethod
    def test_empty_group_name() -> None:
        """Test that empty group names raise an error"""
        with pytest.raises(typer.BadParameter, match='Group names cannot be empty'):
            _parse_groups_argument('[test,,dev]')

    @staticmethod
    def test_whitespace_only_group() -> None:
        """Test that whitespace-only group names raise an error"""
        with pytest.raises(typer.BadParameter, match='Group names cannot be empty'):
            _parse_groups_argument('[test,  ,dev]')
