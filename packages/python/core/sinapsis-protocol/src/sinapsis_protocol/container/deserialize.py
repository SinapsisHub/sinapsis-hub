import datetime as dt
import hashlib
from typing import Any
from uuid import UUID

from sinapsis_protocol.codecs.registry import AdapterRegistry, default_registry
from sinapsis_protocol.dataclass.registry import decode_dataclass
from sinapsis_protocol.errors import InvalidPacketError, PayloadTooLargeError, UnsupportedProtocolVersionError
from sinapsis_protocol.types import DecodeContext
from sinapsis_protocol.wire.constants import PayloadKind, ProtocolSentinel, WireKind
from sinapsis_protocol.wire.format import decode_message, model_from_wire
from sinapsis_protocol.wire.models import (
    ArrayMetadata,
    ArtifactPayload,
    DataFrameMetadata,
    DateTimeMetadata,
    ImageMetadata,
    InlinePayload,
    Metadata,
    Payload,
    PayloadDescriptor,
    TextMetadata,
    TorchMetadata,
    TransportValue,
)

_METADATA_TYPES = {
    ("array", "numpy"): ArrayMetadata,
    ("array", "torch"): TorchMetadata,
    ("image", "opencv"): ImageMetadata,
    ("dataframe", "pandas"): DataFrameMetadata,
    ("dataframe", "polars"): DataFrameMetadata,
    ("datetime", "builtin"): DateTimeMetadata,
    ("text", "builtin"): TextMetadata,
}


def _payload_from_wire(value: dict[str, Any]) -> Payload:
    kind = PayloadKind(value["kind"])
    inline = model_from_wire(InlinePayload, value["inline"]) if value.get("inline") is not None else None
    artifact = model_from_wire(ArtifactPayload, value["artifact"]) if value.get("artifact") is not None else None
    extras = value.get("extras")
    return Payload(kind=kind, inline=inline, artifact=artifact, extras=dict(extras or {}))


def _transport_from_wire(value: dict[str, Any]) -> TransportValue:
    descriptor = model_from_wire(
        PayloadDescriptor, {key: value[key] for key in ("kind", "version", "library", "codec") if key in value}
    )
    metadata_type = _METADATA_TYPES.get((descriptor.kind, descriptor.library), Metadata)
    metadata = model_from_wire(metadata_type, value.get("metadata", {}))
    payload = _payload_from_wire(value.get("payload", {}))
    return TransportValue(descriptor=descriptor, metadata=metadata, payload=payload)


def _denormalize(value: Any, context: DecodeContext, registry: AdapterRegistry, depth: int = 0) -> Any:
    if depth > context.limits.max_nesting_depth:
        raise PayloadTooLargeError("Maximum nesting depth exceeded")
    if isinstance(value, list):
        if len(value) > context.limits.max_collection_length:
            raise PayloadTooLargeError("Collection exceeds max_collection_length")
        return [_denormalize(v, context, registry, depth + 1) for v in value]
    if isinstance(value, dict):
        if "__type__" in value:
            kind = value["__type__"]
            if kind == WireKind.DATACLASS:
                decode = lambda item, ctx, child_depth: _denormalize(item, ctx, registry, child_depth)
                return decode_dataclass(value, decode, registry.dataclasses, context, depth)
            transport = _transport_from_wire({**value, "kind": kind})
            if kind == WireKind.UUID:
                raw = transport.payload.extras.get("value") if transport.payload.extras else None
                return UUID(raw)
            if kind == WireKind.DATETIME:
                raw = transport.payload.extras.get("value") if transport.payload.extras else None
                value_type = (
                    transport.metadata.value_type if isinstance(transport.metadata, DateTimeMetadata) else "datetime"
                )
                if value_type == "datetime":
                    return dt.datetime.fromisoformat(raw)
                if value_type == "date":
                    return dt.date.fromisoformat(raw)
                return dt.time.fromisoformat(raw)
            if kind in (WireKind.BINARY, WireKind.FILE):
                payload = transport.payload
                if payload.kind is PayloadKind.INLINE and payload.inline is not None:
                    data = payload.inline.data
                    if payload.inline.sha256 and hashlib.sha256(data).hexdigest() != payload.inline.sha256:
                        raise InvalidPacketError("Binary checksum mismatch")
                    return data
                if payload.artifact is None:
                    raise InvalidPacketError("Artifact payload is missing its reference")
                return context.artifact_store.read_bytes(payload.artifact.artifact)
            return registry.decode(transport, context)
        return {
            _denormalize(k, context, registry, depth + 1): _denormalize(v, context, registry, depth + 1)
            for k, v in value.items()
        }
    return value


def deserialize(
    data: bytes, *, registry: AdapterRegistry | None = None, artifact_store: Any = None, config: Any = None
) -> object:
    from sinapsis_protocol.container.serialize import SerializationConfig

    config = config or SerializationConfig()
    registry = registry or default_registry()
    if artifact_store is None:
        from sinapsis_protocol.container.serialize import _default_store

        artifact_store = _default_store()
    unpacked = decode_message(data, max_packet_bytes=config.limits.max_packet_bytes)
    if isinstance(unpacked, ProtocolSentinel):
        return unpacked
    if not isinstance(unpacked, dict) or unpacked.get("protocol") != "sinapsis-data":
        raise InvalidPacketError("Missing or invalid protocol envelope")
    if int(unpacked.get("major", -1)) != 1:
        raise UnsupportedProtocolVersionError(f"Unsupported protocol major: {unpacked.get('major')}")
    if unpacked.get("kind") != WireKind.CONTAINER.value:
        raise InvalidPacketError("Unsupported packet kind")
    context = DecodeContext(artifact_store, config.limits, frozenset())
    return _denormalize(unpacked.get("payload"), context, registry)
