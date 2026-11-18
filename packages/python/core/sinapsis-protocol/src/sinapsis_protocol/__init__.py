"""Public API for the Sinapsis universal data transport protocol."""

from sinapsis_protocol.artifacts import ArtifactRef, ArtifactStore, LocalArtifactStore
from sinapsis_protocol.codecs import AdapterRegistry, AdapterSpec, default_registry
from sinapsis_protocol.container import (
    SerializationConfig,
    deserialize,
    deserialize_data_container,
    serialize,
    serialize_data_container,
)
from sinapsis_protocol.errors import (
    ArtifactError,
    InvalidPacketError,
    InvalidPayloadError,
    PayloadTooLargeError,
    ProtocolError,
    UnsupportedProtocolVersionError,
    UnsupportedTypeError,
)
from sinapsis_protocol.wire import (
    PROTOCOL_EXT_CODE,
    PROTOCOL_MAJOR,
    PROTOCOL_MINOR,
    PROTOCOL_NAME,
    AgentStatus,
    EventType,
    PayloadCodec,
    PayloadKind,
    ProtocolSentinel,
    RequestType,
    WireKind,
    decode_sentinel,
    encode_sentinel,
    is_sentinel_packet,
    split_websocket_frame,
)
from sinapsis_protocol.wire.envelope import EnvelopeError, SSEEnvelope, deserialize_sse_envelope, serialize_sse_envelope

__version__ = "0.1.0"

__all__ = [
    "AdapterRegistry",
    "AdapterSpec",
    "ArtifactError",
    "ArtifactRef",
    "ArtifactStore",
    "AgentStatus",
    "EnvelopeError",
    "EventType",
    "InvalidPacketError",
    "InvalidPayloadError",
    "LocalArtifactStore",
    "PayloadCodec",
    "PayloadKind",
    "PayloadTooLargeError",
    "PROTOCOL_EXT_CODE",
    "PROTOCOL_MAJOR",
    "PROTOCOL_MINOR",
    "PROTOCOL_NAME",
    "ProtocolError",
    "ProtocolSentinel",
    "RequestType",
    "SerializationConfig",
    "UnsupportedProtocolVersionError",
    "UnsupportedTypeError",
    "WireKind",
    "SSEEnvelope",
    "serialize_sse_envelope",
    "deserialize_sse_envelope",
    "default_registry",
    "deserialize",
    "deserialize_data_container",
    "serialize",
    "serialize_data_container",
    "is_sentinel_packet",
    "encode_sentinel",
    "decode_sentinel",
    "split_websocket_frame",
]
