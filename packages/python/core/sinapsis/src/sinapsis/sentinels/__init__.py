"""Sentinel implementation for Sinapsis-specific use cases.
"""

from typing import ClassVar


class SinapsisSentinel:
    """A sentinel class used to signal specific conditions in Sinapsis.

    Attributes:
        value: The internal value used to represent the sentinel.
    """

    __instances: ClassVar[dict[str, "SinapsisSentinel"]] = {}

    def __new__(cls, value: str) -> "SinapsisSentinel":
        """Creates a new instance or returns an existing one for the given value.

        Args:
            value: A string representing the sentinel's value.

        Returns:
            The singleton instance for the given value.
        """
        if not isinstance(value, str):
            raise TypeError(f"Expected {value} to be a string.")

        if value not in cls.__instances:
            cls.__instances[value] = super().__new__(cls)
            instance = cls.__instances[value]
            instance.__value = value
        return cls.__instances[value]

    def __init__(self, value: str) -> None:
        self.__value = value

    def __repr__(self) -> str:
        # return f"SinapsisSentinel({self.value})"
        return self.value

    def __eq__(self, other: object) -> bool:
        """Checks equality with another sentinel.

        Args:
            other: Another sentinel to compare with.

        Returns:
            True if the values are equal, False otherwise.
        """
        if isinstance(other, SinapsisSentinel):
            return self.value == other.value
        return False

    @property
    def value(self) -> str:
        return self.__value


SENTINEL_GENERIC_KEY = SinapsisSentinel("SENTINEL_GENERIC_KEY")
SINAPSIS_NOT_SET = SinapsisSentinel("SINAPSIS_NOT_SET")
SINAPSIS_EMPTY_CONTAINER = SinapsisSentinel("SINAPSIS_EMPTY_CONTAINER")

__all__ = [
    "SENTINEL_GENERIC_KEY",
    "SINAPSIS_EMPTY_CONTAINER",
    "SINAPSIS_NOT_SET",
    "SinapsisSentinel",
]
