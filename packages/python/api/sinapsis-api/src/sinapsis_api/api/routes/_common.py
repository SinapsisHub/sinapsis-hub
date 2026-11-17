"""Shared helpers for stateless FastAPI route handlers."""

import base64
import binascii
import uuid
from typing import Any

from fastapi import HTTPException, WebSocket, WebSocketDisconnect
from sinapsis.logging import sinapsis_logger

from sinapsis_api.client import RouterClient, SubscriberLaggedError
from sinapsis_api.constants import ControlType, RouterError

router_client = RouterClient()


def command(control_type: ControlType, **values: Any) -> dict[str, Any]:
    """Create an idempotency-keyed Router control request."""
    return {"type": control_type.value, "command_id": str(uuid.uuid4()), **values}


def require_success(response: dict[str, Any]) -> dict[str, Any]:
    """Translate Router control errors to HTTP errors."""
    if response.get("ok"):
        sinapsis_logger.debug("Router returned success response ", response)
        return response

    error = response.get("error")

    status_code = {
        RouterError.NOT_FOUND.value: 404,
        RouterError.CONFLICT.value: 409,
        RouterError.UNAVAILABLE.value: 503,
    }.get(error, 500)

    detail = response.get("detail", error)

    sinapsis_logger.error("Router returned API error %s: %s", error, detail)

    raise HTTPException(status_code=status_code, detail=detail)


def decode_job_payload(payload: str | None) -> bytes | None:
    """Decode an HTTP-safe serialized DataContainer without deserializing it."""
    if payload is None:
        return None

    try:
        return base64.b64decode(payload, validate=True)
    except (ValueError, binascii.Error) as exception:
        sinapsis_logger.error("Invalid base64 job payload: %s", exception)
        raise HTTPException(status_code=422, detail="payload must be valid base64") from exception


def encode_replay_body(events: tuple[Any, ...]) -> bytes:
    """Encode bounded events as length-prefixed WebSocket-compatible frames."""
    chunks: list[bytes] = []

    for event in events:
        frame = event.websocket_frame()
        chunks.extend((len(frame).to_bytes(4, "big"), frame))

    return b"".join(chunks)


async def stream_agent_events(
    websocket: WebSocket, *, agent_id: str, after: int | None = None, job_id: str | None = None
) -> None:
    """Stream Router events to an accepted WebSocket."""
    await websocket.accept()

    try:
        async for event in router_client.subscribe(agent_id=agent_id, after=after, job_id=job_id):
            await websocket.send_bytes(event.websocket_frame())

    except SubscriberLaggedError as exception:
        sinapsis_logger.warning("WebSocket subscriber lagged for agent %s: %s", agent_id, exception.metadata)
        await websocket.close(code=4008, reason="subscriber lagged; reconnect using the last processed cursor")

    except WebSocketDisconnect:
        sinapsis_logger.info("WebSocket disconnected for agent %s.", agent_id)

    except Exception as exception:
        sinapsis_logger.exception("WebSocket event stream failed for agent %s. Exc: %s.", agent_id, exception)
        await websocket.close(code=1011, reason="event stream failed")
