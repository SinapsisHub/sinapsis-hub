"""Transport framing for control messages and opaque event payloads."""

from dataclasses import dataclass
from typing import Any

import msgpack
from sinapsis.logging import sinapsis_logger

PROTOCOL_VERSION = 1


def pack_control(value: dict[str, Any]) -> bytes:
    """Serialize a transport control message."""
    return msgpack.packb(value, use_bin_type=True)


def unpack_control(data: bytes | memoryview) -> dict[str, Any]:
    """Deserialize a transport control message."""
    value = msgpack.unpackb(data, raw=False, strict_map_key=False)
    if not isinstance(value, dict):
        sinapsis_logger.error("Control message must be a map.")
        raise ValueError("Control message must be a map.")
    return value


@dataclass(frozen=True, slots=True)
class EventRecord:
    """Router metadata plus an opaque serialized SSEEnvelope."""

    stream_id: str
    cursor: int
    created_ns: int
    agent_id: str
    instance_id: str
    job_id: str | None
    payload: bytes

    @property
    def size_bytes(self) -> int:
        """Return the retained payload size in bytes."""
        return len(self.payload)

    def metadata(self) -> dict[str, Any]:
        """Return transport metadata without inspecting the payload."""
        return {
            "version": PROTOCOL_VERSION,
            "stream_id": self.stream_id,
            "cursor": self.cursor,
            "created_ns": self.created_ns,
            "agent_id": self.agent_id,
            "instance_id": self.instance_id,
            "job_id": self.job_id,
        }

    def zmq_frames(self) -> tuple[bytes, bytes]:
        """Return metadata and opaque payload frames."""
        return pack_control(self.metadata()), self.payload

    def websocket_frame(self) -> bytes:
        """Build a binary WebSocket frame from a MessagePack header and opaque payload.

        The MessagePack metadata object is self-delimiting. The serialized
        SSEEnvelope is appended byte-for-byte and is never decoded, encoded,
        or included inside another serialization model.
        """
        return pack_control(self.metadata()) + self.payload


def split_websocket_frame(frame: bytes | memoryview) -> tuple[dict[str, Any], memoryview]:
    """Split one event frame without touching the serialized SSEEnvelope.

    Exactly one MessagePack object is consumed from the start of ``frame``.
    Every byte after that object is returned as the opaque event payload.

    Args:
        frame: Binary frame containing a MessagePack metadata header followed
            immediately by a serialized SSEEnvelope.

    Returns:
        A tuple containing the decoded transport metadata and a zero-copy view
        over the original serialized SSEEnvelope bytes.

    Raises:
        ValueError: If the frame does not start with a valid metadata map or
            contains no event payload.
    """
    view = memoryview(frame)
    unpacker = msgpack.Unpacker(raw=False, strict_map_key=False)
    unpacker.feed(view)

    try:
        metadata = next(unpacker)
    except (StopIteration, msgpack.UnpackException, ValueError) as exception:
        sinapsis_logger.exception("Invalid event frame metadata.")
        raise ValueError("Invalid event frame metadata.") from exception

    if not isinstance(metadata, dict):
        sinapsis_logger.error("Event frame metadata must be a map.")
        raise ValueError("Event frame metadata must be a map.")

    metadata_end = unpacker.tell()
    if metadata_end >= len(view):
        sinapsis_logger.error("Event frame does not contain an SSEEnvelope payload.")
        raise ValueError("Event frame does not contain an SSEEnvelope payload.")

    return metadata, view[metadata_end:]
