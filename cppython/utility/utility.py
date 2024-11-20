"""Utility definitions"""

import re
from typing import Any, NamedTuple, NewType

TypeName = NewType('TypeName', str)
TypeGroup = NewType('TypeGroup', str)


class TypeID(NamedTuple):
    """Represents a type ID with a name and group."""

    name: TypeName
    group: TypeGroup


_canonicalize_regex = re.compile(r'((?<=[a-z])[A-Z]|(?<!\A)[A-Z](?=[a-z]))')


def canonicalize_name(name: str) -> TypeID:
    """Extracts the type identifier from an input string

    Args:
        name: The string to parse

    Returns:
        The type identifier
    """
    sub = re.sub(_canonicalize_regex, r' \1', name)
    values = sub.split(' ')
    result = ''.join(values[:-1])
    return TypeID(TypeName(result.lower()), TypeGroup(values[-1].lower()))


def canonicalize_type(input_type: type[Any]) -> TypeID:
    """Extracts the plugin identifier from a type

    Args:
        input_type: The input type to resolve

    Returns:
        The type identifier
    """
    return canonicalize_name(input_type.__name__)
