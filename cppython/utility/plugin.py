"""Defines the base plugin type and related types."""

from typing import Protocol

from cppython.utility.utility import TypeGroup, TypeID, TypeName, canonicalize_name


class Plugin(Protocol):
    """A protocol for defining a plugin type"""

    @classmethod
    def id(cls) -> TypeID:
        """The type identifier for the plugin

        Returns:
            The type identifier
        """
        return canonicalize_name(cls.__name__)

    @classmethod
    def name(cls) -> TypeName:
        """The name of the plugin

        Returns:
            The name
        """
        return cls.id().name

    @classmethod
    def group(cls) -> TypeGroup:
        """The group of the plugin

        Returns:
            The group
        """
        return cls.id().group
