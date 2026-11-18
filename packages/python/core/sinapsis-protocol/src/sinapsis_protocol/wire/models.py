from typing import Any

from sinapsis.data_transport import dataclass

from sinapsis_protocol.artifacts.ref import ArtifactRef
from sinapsis_protocol.wire.constants import PayloadCodec, PayloadKind


@dataclass(frozen=True, slots=True)
class Metadata:
    """Structured protocol metadata with an escape hatch for future fields."""

    extras: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.extras is None:
            object.__setattr__(self, "extras", {})


@dataclass(frozen=True, slots=True)
class ArrayMetadata(Metadata):
    shape: tuple[int, ...] = ()
    dtype: str = ""
    order: str = "C"


@dataclass(frozen=True, slots=True)
class TorchMetadata(ArrayMetadata):
    device: str = "cpu"
    requires_grad: bool = False


@dataclass(frozen=True, slots=True)
class ImageMetadata(Metadata):
    shape: tuple[int, ...] = ()
    format: str = "png"


@dataclass(frozen=True, slots=True)
class DataFrameMetadata(Metadata):
    format: str = "arrow-ipc-stream"


@dataclass(frozen=True, slots=True)
class TextMetadata(Metadata):
    encoding: str = "utf-8"


@dataclass(frozen=True, slots=True)
class DateTimeMetadata(Metadata):
    value_type: str = "datetime"


@dataclass(frozen=True, slots=True)
class PayloadDescriptor:
    kind: str
    version: int = 1
    library: str | None = None
    codec: PayloadCodec = PayloadCodec.NONE


@dataclass(frozen=True, slots=True)
class InlinePayload:
    data: bytes
    sha256: str | None = None


@dataclass(frozen=True, slots=True)
class ArtifactPayload:
    artifact: ArtifactRef


@dataclass(frozen=True, slots=True)
class Payload:
    kind: PayloadKind
    inline: InlinePayload | None = None
    artifact: ArtifactPayload | None = None
    extras: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.extras is None:
            object.__setattr__(self, "extras", {})


@dataclass(frozen=True, slots=True)
class TransportValue:
    descriptor: PayloadDescriptor
    metadata: Metadata
    payload: Payload
