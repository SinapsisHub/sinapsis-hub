"""MessagePack encoding of the Sinapsis data wire format."""

import dataclasses
from enum import Enum
from typing import Any, Mapping, TypeVar, get_args, get_origin, get_type_hints

import msgpack

from sinapsis_protocol.errors import InvalidPacketError, InvalidPayloadError
from sinapsis_protocol.wire.constants import (
    PROTOCOL_EXT_CODE,
    ProtocolSentinel,
)

T = TypeVar("T")


def _to_wire(value: Any) -> Any:
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        result: dict[str, Any] = {}
        for field in dataclasses.fields(value):
            field_value = getattr(value, field.name)
            if field_value is None or field_value == {}:
                continue
            result[field.name] = _to_wire(field_value)
        return result
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {_to_wire(k): _to_wire(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_to_wire(item) for item in value]
    return value


def _from_wire(cls: type[T], value: Any) -> T:
    if not dataclasses.is_dataclass(cls) or not isinstance(value, Mapping):
        raise InvalidPacketError(f"Expected a mapping for {cls!r}")
    hints = get_type_hints(cls)
    fields = {field.name: field for field in dataclasses.fields(cls)}
    kwargs: dict[str, Any] = {}
    extras: dict[str, Any] = {}

    for key, raw in value.items():
        field = fields.get(key)
        if field is None:
            extras[key] = raw
            continue
        kwargs[key] = _decode_annotation(hints.get(key, field.type), raw)

    if "extras" in fields:
        existing = kwargs.get("extras") or {}
        kwargs["extras"] = {**extras, **existing}
    elif extras:
        raise InvalidPacketError(f"Unknown fields for {cls.__name__}: {sorted(extras)}")
    try:
        return cls(**kwargs)
    except Exception as exc:
        raise InvalidPacketError(f"Could not construct {cls.__name__}") from exc


def _decode_annotation(annotation: Any, value: Any) -> Any:
    if value is None:
        return None
    origin = get_origin(annotation)
    args = get_args(annotation)
    if origin in (list, tuple, set, frozenset):
        item_type = args[0] if args else Any
        decoded = [_decode_annotation(item_type, item) for item in value]
        return tuple(decoded) if origin is tuple else origin(decoded)
    if origin is dict:
        key_type, value_type = args or (Any, Any)
        return {_decode_annotation(key_type, key): _decode_annotation(value_type, item) for key, item in value.items()}
    if origin is not None and origin is type(None):
        return value
    if origin is not None and origin is getattr(__import__("types"), "UnionType", object):
        for candidate in args:
            if candidate is type(None):
                continue
            try:
                return _decode_annotation(candidate, value)
            except Exception:
                pass
        return value
    if origin is getattr(__import__("typing"), "Union", object):
        for candidate in args:
            if candidate is type(None):
                continue
            try:
                return _decode_annotation(candidate, value)
            except Exception:
                pass
        return value
    if isinstance(annotation, type) and issubclass(annotation, Enum):
        return annotation(value)
    if isinstance(annotation, type) and dataclasses.is_dataclass(annotation):
        return _from_wire(annotation, value)
    return value


def model_to_wire(value: Any, *, flatten_transport: bool = False) -> dict[str, Any]:
    """Convert a typed protocol model to a MessagePack-compatible map."""
    result = _to_wire(value)
    if flatten_transport:
        from sinapsis_protocol.wire.models import TransportValue

        if not isinstance(value, TransportValue):
            raise TypeError("flatten_transport requires a TransportValue")
        descriptor = result.pop("descriptor")
        result["__type__"] = descriptor.pop("kind")
        result.update(descriptor)
    return result


def model_from_wire(cls: type[T], value: Mapping[str, Any]) -> T:
    """Construct a typed protocol model from a MessagePack-compatible map."""
    return _from_wire(cls, value)


def encode_sentinel(state: ProtocolSentinel) -> bytes:
    return msgpack.packb(msgpack.ExtType(PROTOCOL_EXT_CODE, bytes([int(state)])), use_bin_type=True)


def decode_sentinel(data: bytes) -> int:
    try:
        value = msgpack.unpackb(data, raw=False)
    except (msgpack.ExtraData, msgpack.FormatError, msgpack.UnpackException) as exc:
        raise InvalidPayloadError("Invalid sentinel encoding") from exc

    if not isinstance(value, msgpack.ExtType):
        raise InvalidPayloadError("Expected a MessagePack extension value")

    if value.code != PROTOCOL_EXT_CODE or len(value.data) != 1:
        raise InvalidPayloadError("Invalid protocol sentinel")

    sentinel = value.data[0]

    if sentinel not in ProtocolSentinel._value2member_map_:
        raise InvalidPayloadError(f"Unknown protocol sentinel: {sentinel}")

    return sentinel


def decode_message(data: bytes, *, max_packet_bytes: int) -> Any:
    if len(data) > max_packet_bytes:
        raise InvalidPacketError("Packet exceeds max_packet_bytes")

    def ext_hook(code: int, payload: bytes) -> object:
        if code != PROTOCOL_EXT_CODE or len(payload) != 1:
            raise InvalidPacketError(f"Unknown MessagePack extension code: {code}")
        try:
            return ProtocolSentinel(payload[0])
        except ValueError as exc:
            raise InvalidPacketError(f"Unknown Sinapsis sentinel: {payload[0]}") from exc

    return msgpack.unpackb(data, raw=False, ext_hook=ext_hook, strict_map_key=False)


def encode_message(value: Mapping[str, Any], *, max_packet_bytes: int) -> bytes:
    packet = msgpack.packb(value, use_bin_type=True, strict_types=False)
    if len(packet) > max_packet_bytes:
        raise InvalidPacketError("Packet exceeds max_packet_bytes")
    return packet
