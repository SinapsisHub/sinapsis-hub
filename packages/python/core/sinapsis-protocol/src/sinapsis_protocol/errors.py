"""Protocol-specific exceptions."""


class ProtocolError(Exception):
    """Base class for protocol errors."""


class InvalidPacketError(ProtocolError):
    """Packet framing or structural validation failed."""


class InvalidPayloadError(ProtocolError):
    """A payload is malformed or inconsistent with its metadata."""


class UnsupportedProtocolVersionError(ProtocolError):
    """The packet uses an unsupported protocol version."""


class UnsupportedTypeError(ProtocolError):
    """No trusted codec or dataclass registration exists for a type."""


class PayloadTooLargeError(ProtocolError):
    """A configured resource limit was exceeded."""


class ArtifactError(ProtocolError):
    """Artifact storage or integrity verification failed."""
