"""ZeroMQ client used by stateless API workers."""

import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

import zmq
import zmq.asyncio
from sinapsis.logging import sinapsis_logger

from sinapsis_api.constants import StreamFrame, StreamOperation
from sinapsis_api.env_vars import (
    SINAPSIS_API_ROUTER_API_ENDPOINT,
    SINAPSIS_API_ROUTER_STREAM_ENDPOINT,
    SINAPSIS_API_ZMQ_RECEIVE_HWM,
    SINAPSIS_API_ZMQ_SEND_HWM,
)
from sinapsis_api.protocol import EventRecord, pack_control, unpack_control


@dataclass(frozen=True, slots=True)
class ReplayPage:
    """Bounded replay page plus Router-provided cursor metadata."""

    events: tuple[EventRecord, ...]
    metadata: dict[str, Any]


class SubscriberLaggedError(RuntimeError):
    """Raised when a live subscriber cannot keep up with its bounded queue."""

    def __init__(self, metadata: dict[str, Any]) -> None:
        self.metadata = metadata
        super().__init__(f"Subscriber lagged: {metadata}.")


class RouterClient:
    """Short-lived request sockets and dedicated stream sockets for API workers."""

    def __init__(
        self,
        api_endpoint: str = SINAPSIS_API_ROUTER_API_ENDPOINT,
        stream_endpoint: str = SINAPSIS_API_ROUTER_STREAM_ENDPOINT,
    ) -> None:
        self.context = zmq.asyncio.Context.instance()
        self.api_endpoint = api_endpoint
        self.stream_endpoint = stream_endpoint

    async def request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Send one control request to the Router."""
        socket = self._dealer_socket("api", self.api_endpoint)
        try:
            await socket.send(pack_control(request))
            return unpack_control(await socket.recv())
        except Exception:
            sinapsis_logger.exception("Router control request failed.")
            raise
        finally:
            socket.close()

    async def replay(
        self, *, agent_id: str, after: int, job_id: str | None = None, limit: int | None = None
    ) -> ReplayPage:
        """Fetch one bounded replay page for an agent stream."""
        parameters: dict[str, Any] = {"agent_id": agent_id, "after": after, "job_id": job_id}
        if limit is not None:
            parameters["limit"] = limit
        events: list[EventRecord] = []
        socket = self._dealer_socket("replay", self.stream_endpoint)
        await socket.send_multipart([StreamOperation.REPLAY.value, pack_control(parameters)])
        try:
            while True:
                frames = await socket.recv_multipart(copy=False)
                frame_type = bytes(frames[0])
                if frame_type == StreamFrame.EVENT.value:
                    events.append(self._event_from_frames(frames[1], frames[2]))
                elif frame_type == StreamFrame.DONE.value:
                    metadata = unpack_control(frames[1].buffer)
                    if not metadata.get("ok", True):
                        sinapsis_logger.error("Router replay error: %s", metadata)
                        raise RuntimeError(metadata.get("detail", "Replay failed."))
                    return ReplayPage(tuple(events), metadata)
        except Exception:
            sinapsis_logger.exception("Replay failed for agent %s.", agent_id)
            raise
        finally:
            socket.close()

    async def subscribe(
        self, *, agent_id: str, after: int | None = None, job_id: str | None = None
    ) -> AsyncIterator[EventRecord]:
        """Replay optionally, then yield live events for one logical agent."""
        parameters = {"agent_id": agent_id, "after": after, "job_id": job_id}
        socket = self._dealer_socket("subscribe", self.stream_endpoint)
        await socket.send_multipart([StreamOperation.SUBSCRIBE.value, pack_control(parameters)])
        try:
            while True:
                frames = await socket.recv_multipart(copy=False)
                frame_type = bytes(frames[0])
                if frame_type == StreamFrame.EVENT.value:
                    yield self._event_from_frames(frames[1], frames[2])
                elif frame_type == StreamFrame.LIVE.value:
                    continue
                elif frame_type == StreamFrame.LAGGED.value:
                    metadata = unpack_control(frames[1].buffer)
                    sinapsis_logger.warning("Subscriber lagged: %s", metadata)
                    raise SubscriberLaggedError(metadata)
        except Exception:
            sinapsis_logger.exception("Subscription ended for agent %s.", agent_id)
            raise
        finally:
            socket.close()

    def _dealer_socket(self, prefix: str, endpoint: str) -> zmq.asyncio.Socket:
        socket = self.context.socket(zmq.DEALER)
        socket.setsockopt(zmq.LINGER, 0)
        socket.setsockopt(zmq.SNDHWM, SINAPSIS_API_ZMQ_SEND_HWM)
        socket.setsockopt(zmq.RCVHWM, SINAPSIS_API_ZMQ_RECEIVE_HWM)
        socket.setsockopt(zmq.IDENTITY, f"{prefix}:{uuid.uuid4()}".encode())
        socket.connect(endpoint)
        return socket

    @staticmethod
    def _event_from_frames(metadata_frame: Any, payload_frame: Any) -> EventRecord:
        metadata = unpack_control(metadata_frame.buffer)
        return EventRecord(
            stream_id=metadata["stream_id"],
            cursor=metadata["cursor"],
            created_ns=metadata["created_ns"],
            agent_id=metadata["agent_id"],
            instance_id=metadata["instance_id"],
            job_id=metadata.get("job_id"),
            payload=bytes(payload_frame.buffer),
        )
