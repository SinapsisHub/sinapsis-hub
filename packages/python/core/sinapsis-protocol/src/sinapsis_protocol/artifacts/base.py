from abc import ABC, abstractmethod
from typing import Any, Mapping

from sinapsis_protocol.artifacts.ref import ArtifactRef


class ArtifactStore(ABC):
    """Runtime interface for storing payload artifacts."""

    @abstractmethod
    def put_bytes(
        self, data: bytes, *, filename: str, mime_type: str | None = None, metadata: Mapping[str, Any] | None = None
    ) -> ArtifactRef:
        raise NotImplementedError

    @abstractmethod
    def put_file(
        self,
        path: str,
        *,
        filename: str | None = None,
        mime_type: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> ArtifactRef:
        raise NotImplementedError

    @abstractmethod
    def read_bytes(self, artifact: ArtifactRef) -> bytes:
        raise NotImplementedError
