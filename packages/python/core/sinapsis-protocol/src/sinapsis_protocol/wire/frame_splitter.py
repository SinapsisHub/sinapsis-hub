from typing import Any

import msgpack
from sinapsis.logging import sinapsis_logger


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
