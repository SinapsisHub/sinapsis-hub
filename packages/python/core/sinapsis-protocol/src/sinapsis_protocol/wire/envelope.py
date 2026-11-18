from __future__ import annotations

from dataclasses import replace
from typing import Any

from sinapsis.data_transport import DataContainer, dataclass

from sinapsis_protocol.codecs.registry import AdapterRegistry, default_registry
from sinapsis_protocol.container.deserialize import _denormalize
from sinapsis_protocol.container.serialize import SerializationConfig, _default_store, _normalize
from sinapsis_protocol.errors import InvalidPacketError, UnsupportedProtocolVersionError
from sinapsis_protocol.types import DecodeContext, EncodeContext
from sinapsis_protocol.wire.constants import (
    PROTOCOL_MAJOR,
    PROTOCOL_MINOR,
    PROTOCOL_NAME,
    AgentStatus,
    EventType,
    RequestType,
    WireKind,
)
from sinapsis_protocol.wire.format import decode_message, encode_message, model_from_wire, model_to_wire


@dataclass(frozen=True, slots=True)
class EnvelopeError:
    code: str
    message: str
    details: str | None = None


@dataclass(frozen=True, slots=True)
class SSEEnvelope:
    """Exchange-level context carried alongside an optional DataContainer."""

    agent_id: str | None = None
    agent_status: AgentStatus | None = None
    data: DataContainer | None = None
    errors: tuple[EnvelopeError, ...] = ()
    event_type: EventType = EventType.DATA
    request_type: RequestType | None = None
    job_id: str | None = None


def _metadata_to_wire(envelope: SSEEnvelope) -> dict[str, Any]:
    value = model_to_wire(replace(envelope, data=None))
    value.pop("data", None)
    value.setdefault("errors", [])
    return value


def serialize_sse_envelope(
    envelope: SSEEnvelope,
    *,
    registry: AdapterRegistry | None = None,
    artifact_store: Any = None,
    config: SerializationConfig | None = None,
) -> bytes:
    """Serialize an SSE exchange envelope and its optional DataContainer."""
    config = config or SerializationConfig()
    registry = registry or default_registry()
    artifact_store = artifact_store or _default_store()
    context = EncodeContext(artifact_store, config.limits, config.inline_binary_limit)

    data = None
    if envelope.data is not None:
        data = _normalize(envelope.data, context, registry, config)

    payload = _metadata_to_wire(envelope)
    payload["data"] = data
    message = {
        "protocol": PROTOCOL_NAME,
        "major": PROTOCOL_MAJOR,
        "minor": PROTOCOL_MINOR,
        "kind": WireKind.SSE_ENVELOPE.value,
        "payload": payload,
    }
    return encode_message(message, max_packet_bytes=config.limits.max_packet_bytes)


def deserialize_sse_envelope(
    data: bytes,
    *,
    registry: AdapterRegistry | None = None,
    artifact_store: Any = None,
    config: SerializationConfig | None = None,
) -> SSEEnvelope:
    """Deserialize an SSE exchange envelope and its optional DataContainer."""
    config = config or SerializationConfig()
    registry = registry or default_registry()
    artifact_store = artifact_store or _default_store()
    unpacked = decode_message(data, max_packet_bytes=config.limits.max_packet_bytes)

    if not isinstance(unpacked, dict) or unpacked.get("protocol") != PROTOCOL_NAME:
        raise InvalidPacketError("Missing or invalid protocol envelope")
    if int(unpacked.get("major", -1)) != PROTOCOL_MAJOR:
        raise UnsupportedProtocolVersionError(f"Unsupported protocol major: {unpacked.get('major')}")
    if unpacked.get("kind") != WireKind.SSE_ENVELOPE.value:
        raise InvalidPacketError("Unsupported packet kind for SSE envelope")

    payload = unpacked.get("payload")
    if not isinstance(payload, dict):
        raise InvalidPacketError("SSE envelope payload must be a mapping")

    envelope_data = payload.get("data")
    context = DecodeContext(artifact_store, config.limits, frozenset())
    restored_data = _denormalize(envelope_data, context, registry) if envelope_data is not None else None
    if restored_data is not None and not isinstance(restored_data, DataContainer):
        raise InvalidPacketError("SSE envelope data must decode to a DataContainer")

    fields = {key: value for key, value in payload.items() if key != "data"}
    envelope = model_from_wire(SSEEnvelope, fields)
    return SSEEnvelope(
        agent_id=envelope.agent_id,
        agent_status=envelope.agent_status,
        data=restored_data,
        errors=envelope.errors,
        event_type=envelope.event_type,
        request_type=envelope.request_type,
        job_id=envelope.job_id,
    )


def inspect_envelope(packet: bytes) -> SSEEnvelope:
    from ._byte_scanner import _Reader

    r = _Reader(packet)

    # outer message
    for _ in range(r.read_map_len()):
        key = r.read_str()

        if key != "payload":
            r.skip()
            continue

        # SSEEnvelope
        result = {}

        for _ in range(r.read_map_len()):
            key = r.read_str()

            if key == "data":
                # The expensive part: do not deserialize it.
                r.skip()
            elif key in {"agent_id", "agent_status", "event_type", "request_type", "job_id"}:
                result[key] = r.read_str()
            else:
                r.skip()

        return SSEEnvelope(**result)

    raise ValueError("missing payload")
