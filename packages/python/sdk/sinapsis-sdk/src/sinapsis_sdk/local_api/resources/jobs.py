"""SDK resource for interacting with local Sinapsis API jobs."""

import base64
from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode, urlparse, urlunparse

import websockets
from sinapsis.agent import AgentSchema
from sinapsis.data_transport import DataContainer
from sinapsis_contracts.local_api.models import (
    AgentResponse,
    ApprovalRequest,
    ApprovalResponse,
    JobActionResponse,
    JobResponse,
    StartJobRequest,
    StartJobResponse,
)
from sinapsis_contracts.local_api.paths import API_AGENT_PATHS, API_JOB_PATHS
from sinapsis_protocol import SSEEnvelope, deserialize_sse_envelope, serialize_data_container, split_websocket_frame

from sinapsis_sdk.common.base_resource_client import BaseClientResource


@dataclass(frozen=True)
class LocalJobEvent:
    """A decoded local API event and its transport metadata."""

    envelope: SSEEnvelope
    metadata: dict[str, Any]


class LocalJobsResource(BaseClientResource):
    """Provides operations for local Sinapsis API jobs."""

    def __init__(self, http) -> None:
        super().__init__(http, API_JOB_PATHS.base)

    async def submit(self, agent_definition: AgentSchema) -> StartJobResponse:
        """Create an agent and submit a job."""

        agent_response = await self._http.post(
            f"{API_AGENT_PATHS.base}{API_AGENT_PATHS.start}", json=agent_definition.model_dump(mode="json")
        )

        agent = AgentResponse.model_validate(agent_response)

        serialized = serialize_data_container(DataContainer())

        request = StartJobRequest(agent_id=agent.agent_id, payload=base64.b64encode(serialized).decode("ascii"))

        response = await self._http.post(self._path(API_JOB_PATHS.start), json=request.model_dump(mode="json"))

        return StartJobResponse.model_validate(response)

    async def get_status(self, job_id: str) -> JobResponse:
        """Retrieve the current status of a local job."""
        p = self._path(API_JOB_PATHS.job, job_id=job_id)
        print(f" path is : {p}")
        response = await self._http.get(self._path(API_JOB_PATHS.job, job_id=job_id))

        return JobResponse.model_validate(response)

    async def get_result(self, job_id: str) -> list[LocalJobEvent]:
        """Retrieve and deserialize retained job events."""
        print(f"job_id: {job_id} \n\n")

        job = await self.get_status(job_id)

        path = f"{API_AGENT_PATHS.base}{API_AGENT_PATHS.events.format(agent_id=job.agent_id)}"
        print(f"path: {path} \n\n")

        body = await self._http.get(path, params={"after": 0, "job_id": job_id}, raw=True)

        return list(self._decode_replay_body(body))

    async def stream_results(self, job_id: str, *, after: int = 0) -> AsyncIterator[LocalJobEvent]:
        """Stream decoded local job events over WebSocket."""

        path = self._path(API_JOB_PATHS.events, job_id=job_id)

        url = self._websocket_url(path)

        query = urlencode({"after": after})

        async with websockets.connect(f"{url}?{query}", max_size=None) as websocket:
            async for raw_frame in websocket:
                if not isinstance(raw_frame, bytes):
                    continue

                yield self._decode_event(raw_frame)

    async def cancel(self, job_id: str) -> JobActionResponse:
        """Cancel a running local job."""

        response = await self._http.post(self._path(API_JOB_PATHS.cancel, job_id=job_id))

        return JobActionResponse.model_validate(response)

    async def feedback(self, job_id: str, request: ApprovalRequest) -> ApprovalResponse:
        """Submit approval feedback for a local job."""

        response = await self._http.post(
            self._path(API_JOB_PATHS.feedback, job_id=job_id), json=request.model_dump(mode="json")
        )

        return ApprovalResponse.model_validate(response)

    @staticmethod
    def _decode_event(frame: bytes | memoryview) -> LocalJobEvent:
        """Deserialize an event frame and preserve its metadata."""

        metadata, payload = split_websocket_frame(frame)

        envelope = deserialize_sse_envelope(bytes(payload))

        return LocalJobEvent(envelope=envelope, metadata=metadata)

    @classmethod
    def _decode_replay_body(cls, body: bytes) -> Iterator[LocalJobEvent]:
        """Decode length-prefixed event frames from a replay response."""

        offset = 0

        while offset < len(body):
            if offset + 4 > len(body):
                raise ValueError("Truncated replay frame length.")

            frame_length = int.from_bytes(body[offset : offset + 4], "big")

            offset += 4

            frame_end = offset + frame_length

            if frame_end > len(body):
                raise ValueError("Truncated replay frame.")

            frame = memoryview(body)[offset:frame_end]

            yield cls._decode_event(frame)

            offset = frame_end

    def _websocket_url(self, path: str) -> str:
        """Convert the configured HTTP API URL into a WebSocket URL."""

        base_url = str(self._http.base_url).rstrip("/")

        parsed = urlparse(base_url)

        scheme = {"http": "ws", "https": "wss"}.get(parsed.scheme)

        if scheme is None:
            raise ValueError(f"Unsupported API URL scheme: {parsed.scheme!r}")

        return urlunparse(parsed._replace(scheme=scheme, path=f"{parsed.path.rstrip('/')}{path}"))
