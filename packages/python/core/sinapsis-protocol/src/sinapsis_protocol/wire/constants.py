from enum import IntEnum, StrEnum

PROTOCOL_NAME = "sinapsis-data"
PROTOCOL_MAJOR = 1
PROTOCOL_MINOR = 0
PROTOCOL_EXT_CODE = 42


class WireKind(StrEnum):
    CONTAINER = "container"
    DATACLASS = "dataclass"
    BINARY = "binary"
    FILE = "file"
    UUID = "uuid"
    DATETIME = "datetime"
    ARRAY = "array"
    DATAFRAME = "dataframe"
    IMAGE = "image"
    SSE_ENVELOPE = "sse-envelope"


class PayloadKind(StrEnum):
    INLINE = "inline"
    ARTIFACT = "artifact"


class PayloadCodec(StrEnum):
    NONE = "none"
    RAW = "raw"
    ARROW = "arrow"


class AgentStatus(StrEnum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


class EventType(StrEnum):
    DATA = "data"
    STATUS = "status"
    ERROR = "error"
    COMPLETE = "complete"
    HEARTBEAT = "heartbeat"
    CALLBACK = "callback"  # Human in the loop


class RequestType(StrEnum):
    EXECUTE = "execute"
    STREAM = "stream"
    STATUS = "status"
    CANCEL = "cancel"


class ProtocolSentinel(IntEnum):
    EMPTY_CONTAINER = 1
    EMPTY_PACKET = 2
    NULL_VALUE = 3
    HEARTBEAT = 4
    END_OF_STREAM = 5


def is_sentinel_packet(data: bytes) -> bool:
    """Check if raw byte data represents a MessagePack Protocol Sentinel packet.

    Validates that the input is a 3-byte MessagePack fixext 1 packet (header 0xd4)
    with the sentinel extension type code set to 42.

        data[0] = 0xd4 (fixext 1 header)
        data[1] = 42 (PROTOCOL_EXT_CODE)
        data[2] = int(state) (Payload value)

    Args:
        data: The serialized bytes payload to inspect.

    Returns:
        True if the payload is a valid sentinel packet, False otherwise.
    """
    return len(data) == 3 and data[0] == 0xD4 and data[1] == PROTOCOL_EXT_CODE
