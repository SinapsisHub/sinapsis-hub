from abc import ABC, abstractmethod
from typing import Any, Mapping

from sinapsis.data_transport import dataclass

from sinapsis_protocol.artifacts.base import ArtifactStore
from sinapsis_protocol.wire.models import TransportValue


@dataclass(frozen=True, slots=True)
class SerializationLimits:
    max_packet_bytes: int = 256 * 1024 * 1024 * 100
    max_inline_bytes: int = 16 * 1024 * 1024 * 100
    max_array_bytes: int = 512 * 1024 * 1024 * 100
    max_collection_length: int = 1_000_000
    max_string_bytes: int = 16 * 1024 * 1024 * 100
    max_nesting_depth: int = 64


@dataclass(frozen=True, slots=True)
class EncodeContext:
    # Runtime service objects are intentionally represented as object here so the
    # same model works with both the stdlib and Pydantic-backed Sinapsis dataclass.
    artifact_store: object
    limits: SerializationLimits
    inline_binary_limit: int
    options: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.options is None:
            object.__setattr__(self, "options", {})

    @property
    def store(self) -> ArtifactStore:
        if not isinstance(self.artifact_store, ArtifactStore):
            raise TypeError("artifact_store must implement ArtifactStore")
        return self.artifact_store


@dataclass(frozen=True, slots=True)
class DecodeContext:
    artifact_store: object
    limits: SerializationLimits
    capabilities: frozenset[str]
    options: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.options is None:
            object.__setattr__(self, "options", {})

    @property
    def store(self) -> ArtifactStore:
        if not isinstance(self.artifact_store, ArtifactStore):
            raise TypeError("artifact_store must implement ArtifactStore")
        return self.artifact_store


class Adapter(ABC):
    """Runtime interface implemented by payload codecs."""

    type_name: str
    version: int
    library: str | None

    @classmethod
    @abstractmethod
    def can_encode(cls, value: object) -> bool:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def encode(cls, value: object, context: EncodeContext) -> TransportValue:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def decode(cls, value: TransportValue, context: DecodeContext) -> object:
        raise NotImplementedError
