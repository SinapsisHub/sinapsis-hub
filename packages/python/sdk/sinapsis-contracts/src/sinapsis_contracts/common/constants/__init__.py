from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class _Headers:
    signature: str = "X-Sinapsis-Signature"
    stream_id: str = "X-Sinapsis-Stream-Id"
    oldest_cursor: str = "X-Sinapsis-Oldest-Cursor"
    latest_cursor: str = "X-Sinapsis-Latest-Cursor"
    next_cursor: str = "X-Sinapsis-Next-Cursor"
    truncated: str = "X-Sinapsis-Truncated"
    has_more: str = "X-Sinapsis-Has-More"
    session: str = "X-Sinapsis-Docs-Session"
    service_secret: str = "X-Sinapsis-Service-Secret"


@dataclass(frozen=True, slots=True)
class _MediaTypes:
    events: str = "application/x-sinapsis-events"


@dataclass(frozen=True, slots=True)
class _ApiConstants:
    headers: _Headers = _Headers()
    media_types: _MediaTypes = _MediaTypes()


ApiConstants = _ApiConstants()

__all__ = ["ApiConstants"]
