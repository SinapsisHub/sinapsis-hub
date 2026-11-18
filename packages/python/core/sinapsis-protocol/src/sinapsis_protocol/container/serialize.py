import datetime as dt
import enum
from pathlib import Path
from typing import Any, Mapping
from uuid import UUID

from sinapsis.data_transport import dataclass

from sinapsis_protocol.artifacts.local import LocalArtifactStore
from sinapsis_protocol.codecs.registry import AdapterRegistry, default_registry
from sinapsis_protocol.dataclass.registry import encode_dataclass
from sinapsis_protocol.errors import PayloadTooLargeError
from sinapsis_protocol.types import EncodeContext, SerializationLimits
from sinapsis_protocol.wire.constants import PayloadCodec, PayloadKind, ProtocolSentinel, WireKind
from sinapsis_protocol.wire.format import encode_message, encode_sentinel, model_to_wire
from sinapsis_protocol.wire.models import (
    ArtifactPayload,
    DateTimeMetadata,
    Metadata,
    Payload,
    PayloadDescriptor,
    TransportValue,
)


@dataclass(frozen=True, slots=True)
class SerializationConfig:
    limits: SerializationLimits = SerializationLimits()
    inline_binary_limit: int = 16 * 1024 * 1024
    treat_existing_paths_as_files: bool = False
    treat_extension_strings_as_paths: bool = False


def _default_store() -> LocalArtifactStore:
    return LocalArtifactStore("/tmp/sinapsis-staging", "default", "default")


def _transport_value(
    kind: str, library: str, metadata: Metadata, payload: Payload, codec: PayloadCodec = PayloadCodec.NONE
) -> TransportValue:
    return TransportValue(PayloadDescriptor(kind=kind, version=1, library=library, codec=codec), metadata, payload)


def _file_wire(path: Path, context: EncodeContext) -> TransportValue:
    ref = context.artifact_store.put_file(str(path))
    return _transport_value(
        WireKind.FILE, "builtin", Metadata(), Payload(PayloadKind.ARTIFACT, artifact=ArtifactPayload(ref))
    )


def _normalize(
    value: object, context: EncodeContext, registry: AdapterRegistry, config: SerializationConfig, depth: int = 0
) -> Any:
    if depth > context.limits.max_nesting_depth:
        raise PayloadTooLargeError("Maximum nesting depth exceeded")
    if isinstance(value, Path):
        return model_to_wire(_file_wire(value, context), flatten_transport=True)

    if isinstance(value, str):
        if config.treat_existing_paths_as_files and Path(value).is_file():
            return model_to_wire(_file_wire(Path(value), context), flatten_transport=True)

        if config.treat_extension_strings_as_paths and Path(value).suffix and Path(value).is_file():
            return model_to_wire(_file_wire(Path(value), context), flatten_transport=True)

        if len(value.encode("utf-8")) > context.limits.max_string_bytes:
            raise PayloadTooLargeError("String exceeds max_string_bytes")
        return value

    if value is None or isinstance(value, (bool, int, float, bytes)):
        if isinstance(value, bytes) and len(value) > context.limits.max_inline_bytes:
            ref = context.artifact_store.put_bytes(value, filename="payload.bin", mime_type="application/octet-stream")
            return model_to_wire(
                _transport_value(
                    WireKind.BINARY, "builtin", Metadata(), Payload(PayloadKind.ARTIFACT, artifact=ArtifactPayload(ref))
                ),
                flatten_transport=True,
            )
        return value
    if isinstance(value, UUID):
        return model_to_wire(
            _transport_value(
                WireKind.UUID, "builtin", Metadata(), Payload(PayloadKind.INLINE, extras={"value": str(value)})
            ),
            flatten_transport=True,
        )
    if isinstance(value, (dt.datetime, dt.date, dt.time)):
        return model_to_wire(
            _transport_value(
                WireKind.DATETIME,
                "builtin",
                DateTimeMetadata(value_type=type(value).__name__),
                Payload(PayloadKind.INLINE, extras={"value": value.isoformat()}),
            ),
            flatten_transport=True,
        )
    if isinstance(value, enum.Enum):
        return _normalize(value.value, context, registry, config, depth + 1)
    if __import__("dataclasses").is_dataclass(value) and not isinstance(value, type):
        encode = lambda item, ctx, child_depth: _normalize(item, ctx, registry, config, child_depth)
        return encode_dataclass(value, encode, registry.dataclasses, context, depth)

    if isinstance(value, (list, tuple, set, frozenset)):
        if len(value) > context.limits.max_collection_length:
            raise PayloadTooLargeError("Collection exceeds max_collection_length")
        return [_normalize(v, context, registry, config, depth + 1) for v in value]

    if isinstance(value, Mapping):
        if len(value) > context.limits.max_collection_length:
            raise PayloadTooLargeError("Mapping exceeds max_collection_length")
        if not all(isinstance(k, (str, int, bool, float, bytes)) for k in value):
            raise TypeError("Wire mapping keys must be primitive MessagePack-compatible values")
        return {
            _normalize(k, context, registry, config, depth + 1): _normalize(v, context, registry, config, depth + 1)
            for k, v in value.items()
        }
    return model_to_wire(registry.encode(value, context), flatten_transport=True)


def serialize(
    data: object,
    *,
    registry: AdapterRegistry | None = None,
    artifact_store: Any = None,
    config: SerializationConfig | None = None,
) -> bytes:
    config = config or SerializationConfig()
    registry = registry or default_registry()
    artifact_store = artifact_store or _default_store()
    is_empty = getattr(data, "is_empty", False)
    if callable(is_empty):
        is_empty = is_empty()
    if is_empty:
        return encode_sentinel(ProtocolSentinel.EMPTY_CONTAINER)
    context = EncodeContext(artifact_store, config.limits, config.inline_binary_limit)
    payload = _normalize(data, context, registry, config)
    envelope = {
        "protocol": "sinapsis-data",
        "major": 1,
        "minor": 0,
        "kind": WireKind.CONTAINER.value,
        "payload": payload,
    }
    return encode_message(envelope, max_packet_bytes=config.limits.max_packet_bytes)
