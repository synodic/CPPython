"""Tests for the CMake schema"""

from cppython.plugins.cmake.schema import CacheVariable, VariableType


class TestCacheVariable:
    """Tests for the CacheVariable class"""

    @staticmethod
    def test_cache_variable_bool() -> None:
        """Tests the CacheVariable class with a boolean value"""
        var = CacheVariable(type=VariableType.BOOL, value=True)
        assert var.type == VariableType.BOOL
        assert var.value is True

    @staticmethod
    def test_cache_variable_string() -> None:
        """Tests the CacheVariable class with a string value"""
        var = CacheVariable(type=VariableType.STRING, value='SomeValue')
        assert var.type == VariableType.STRING
        assert var.value == 'SomeValue'

    @staticmethod
    def test_cache_variable_null_type() -> None:
        """Tests the CacheVariable class with a null type"""
        var = CacheVariable(type=None, value='Unset')
        assert var.type is None
        assert var.value == 'Unset'

    @staticmethod
    def test_cache_variable_bool_value_as_string() -> None:
        """Tests the CacheVariable class with a boolean value as a string"""
        # CMake allows bool as "TRUE"/"FALSE" as well
        var = CacheVariable(type=VariableType.BOOL, value='TRUE')
        assert var.value == 'TRUE'

    @staticmethod
    def test_cache_variable_type_optional() -> None:
        """Tests the CacheVariable class with an optional type"""
        # type is optional
        var = CacheVariable(value='SomeValue')
        assert var.type is None
        assert var.value == 'SomeValue'
