"""Test custom schema validation that cannot be verified by the Pydantic validation"""

from tomllib import loads
from typing import Annotated

import pytest
from pydantic import Field

from cppython.core.schema import (
    CPPythonGlobalConfiguration,
    CPPythonLocalConfiguration,
    CPPythonModel,
    PEP621Configuration,
)


class TestSchema:
    """Test validation"""

    class Model(CPPythonModel):
        """Testing Model"""

        aliased_variable: Annotated[bool, Field(alias='aliased-variable', description='Alias test')] = False

    def test_model_construction(self) -> None:
        """Verifies that the base model type has the expected construction behaviors"""
        model = self.Model(**{'aliased_variable': True})
        assert model.aliased_variable is True

        model = self.Model(**{'aliased-variable': True})
        assert model.aliased_variable is True

    def test_model_construction_from_data(self) -> None:
        """Verifies that the base model type has the expected construction behaviors"""
        toml_str = """
        aliased_variable = false\n
        aliased-variable = true
        """

        data = loads(toml_str)
        result = self.Model.model_validate(data)
        assert result.aliased_variable is True

    @staticmethod
    def test_cppython_local() -> None:
        """Ensures that the CPPython local config data can be defaulted"""
        CPPythonLocalConfiguration()

    @staticmethod
    def test_cppython_global() -> None:
        """Ensures that the CPPython global config data can be defaulted"""
        CPPythonGlobalConfiguration()

    @staticmethod
    def test_pep621_version() -> None:
        """Tests the dynamic version validation"""
        with pytest.raises(ValueError, match="'version' is not a dynamic field. It must be defined"):
            PEP621Configuration(name='empty-test')

        with pytest.raises(ValueError, match="'version' is a dynamic field. It must not be defined"):
            PEP621Configuration(name='both-test', version='1.0.0', dynamic=['version'])
