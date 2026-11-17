from typing import Annotated, Protocol, runtime_checkable

from pydantic import Field

ApiKeyMasked = Annotated[str, Field(pattern=r"^sk_[A-Za-z0-9_-]+-\*{5}$")]


@runtime_checkable
class FrozenDataclassProtocol(Protocol):
    """Matches any dataclass instance, enforcing read-only fields."""

    __dataclass_fields__: dict

    # Python Protocols enforce read-only variables via @property getters
    @property
    def __dataclass_params__(self): ...
