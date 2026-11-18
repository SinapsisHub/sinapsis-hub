import hashlib
from typing import TypeVar

from sinapsis_protocol.errors import InvalidPayloadError
from sinapsis_protocol.types import DecodeContext, EncodeContext
from sinapsis_protocol.wire.constants import PayloadCodec, PayloadKind
from sinapsis_protocol.wire.models import ArtifactPayload, InlinePayload, Payload

M = TypeVar("M")


def make_payload(
    data: bytes,
    context: EncodeContext,
    *,
    filename: str,
    mime_type: str | None = None,
    codec: PayloadCodec = PayloadCodec.NONE,
) -> Payload:
    if len(data) > context.limits.max_array_bytes:
        raise ValueError("Payload exceeds max_array_bytes")
    if len(data) <= context.inline_binary_limit:
        return Payload(
            kind=PayloadKind.INLINE, inline=InlinePayload(data=data, sha256=hashlib.sha256(data).hexdigest())
        )
    ref = context.artifact_store.put_bytes(data, filename=filename, mime_type=mime_type)
    return Payload(kind=PayloadKind.ARTIFACT, artifact=ArtifactPayload(ref))


def read_payload(payload: Payload, context: DecodeContext) -> bytes:
    if payload.kind is PayloadKind.INLINE:
        if payload.inline is None:
            raise InvalidPayloadError("Inline payload is missing data")
        data = payload.inline.data
        if payload.inline.sha256 and hashlib.sha256(data).hexdigest() != payload.inline.sha256:
            raise InvalidPayloadError("Payload checksum mismatch")
        return data
    if payload.kind is PayloadKind.ARTIFACT:
        if payload.artifact is None:
            raise InvalidPayloadError("Artifact payload is missing its reference")
        return context.artifact_store.read_bytes(payload.artifact.artifact)
    raise InvalidPayloadError(f"Unsupported payload kind: {payload.kind!r}")
