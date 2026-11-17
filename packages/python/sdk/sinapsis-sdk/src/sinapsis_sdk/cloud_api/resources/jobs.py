"""Job operations for the Sinapsis API."""

import base64
import binascii
from collections.abc import AsyncIterator

from sinapsis.sentinels import SinapsisSentinel
from sinapsis_contracts.cloud_api.models.agents.responses import (
    AgentCancelResponse,
    AgentCreateResponse,
    AgentStatusResponse,
)
from sinapsis_contracts.cloud_api.models.scheduling import ArchivedResultPage
from sinapsis_contracts.cloud_api.paths import AGENT_PATHS
from sinapsis_contracts.cloud_api.paths.scheduling import ARCHIVED_RESULT_PATHS
from sinapsis_contracts.common.sentinels import SINAPSIS_AGENT_FINISHED, SINAPSIS_END_OF_STREAM
from sinapsis_deserialization import MsgpackStreamDecoder, deserialize_sse_message

from sinapsis_sdk.cloud_api.models import AgentDefinition, JobResult
from sinapsis_sdk.common.base_resource_client import BaseClientResource
from sinapsis_sdk.common.exceptions import NotFoundError, ValidationError


class JobsResource(BaseClientResource):
    """Provides operations for Sinapsis jobs."""

    def __init__(self, http) -> None:
        super().__init__(http, AGENT_PATHS.base)

    async def submit(self, agent_definition: AgentDefinition) -> AgentCreateResponse:
        """Submit a new job.

        Args:
            agent_definition: Validated agent definition to submit.

        Returns:
            The submitted job's ID.
        """
        response = await self._http.post(self._path(""), json={"agent_definition": agent_definition})
        return AgentCreateResponse.model_validate(response)

    async def get_status(self, job_id: str, verbose: bool = False) -> AgentStatusResponse:
        """Get the current status of a job.

        Args:
            job_id: ID of the job.
            verbose: Whether to include the full agent definition.

        Returns:
            Current job status.
        """
        response = await self._http.get(self._path(AGENT_PATHS.item, job_id=job_id), params={"verbose": verbose})
        return AgentStatusResponse.model_validate(response)

    async def get_result(self, job_id: str) -> JobResult:
        """Get the final result of a job.

        Args:
            job_id: ID of the job.

        Returns:
            The decoded job result.
        """
        response = await self._http.get(self._path(AGENT_PATHS.results, job_id=job_id), raw=True)
        message = deserialize_sse_message(response)
        if isinstance(message, SinapsisSentinel):
            # Control frames are not results. Let the CLI attempt its archive
            # fallback rather than passing a sentinel to ResultWriter.
            raise NotFoundError("Redis result contains a completion sentinel, not output")
        return message

    async def stream_results(self, job_id: str) -> AsyncIterator[JobResult]:
        decoder = MsgpackStreamDecoder()

        async for chunk in self._http.stream_msgpack("GET", self._path(AGENT_PATHS.stream, job_id=job_id)):
            for message in decoder.sse_decode(chunk):
                if isinstance(message, SinapsisSentinel):
                    # Both agent-finished and stream-end terminate a live stream.
                    # Other Sinapsis sentinels are internal control markers.
                    if message in (SINAPSIS_AGENT_FINISHED, SINAPSIS_END_OF_STREAM):
                        return
                    continue
                yield message

    # Bounded display window: archived streaming must never replay entire history.
    # Redis's own stream-window configuration lives in sinapsis-redis (not in
    # this source archive); callers can pass its configured count explicitly.
    ARCHIVED_STREAM_WINDOW = 100

    async def _recent_archived_frames(self, job_id: str, *, limit: int) -> list:
        """Retrieve a tail window directly from PostgreSQL, not a full-history scan."""
        if not 1 <= limit <= 200:
            raise ValueError("Archived frame window must be between 1 and 200")
        path = ARCHIVED_RESULT_PATHS.base + ARCHIVED_RESULT_PATHS.item.format(job_id=job_id)
        payload = await self._http.get(path, params={"limit": limit, "recent": True})
        return ArchivedResultPage.model_validate(payload).items

    @staticmethod
    def _archive_payload(frame) -> bytes:
        try:
            # PostgreSQL encode(bytea, 'base64') wraps long lines. These
            # RFC 2045 whitespace characters are valid formatting, not data.
            # Keep strict validation for everything else.
            encoded = frame.output_b64.translate(str.maketrans("", "", " \t\r\n"))
            return base64.b64decode(encoded, validate=True)
        except (ValueError, binascii.Error) as exc:
            raise ValidationError("Archived result contains invalid base64") from exc

    async def archived_recent_results(self, job_id: str) -> list[JobResult]:
        """Return the last two actual outputs, skipping any completion sentinels.

        An archived tail can end in control frames. Widen the bounded tail only
        when necessary, without downloading the full result history.
        """
        limit = 2
        while True:
            frames = await self._recent_archived_frames(job_id, limit=limit)
            results = []
            for frame in frames:
                message = deserialize_sse_message(self._archive_payload(frame))
                if not isinstance(message, SinapsisSentinel):
                    results.append(message)
            if len(results) >= 2 or len(frames) < limit or limit == 200:
                return results[-2:]
            limit = min(limit * 2, 200)

    async def archived_stream_results(
        self, job_id: str, *, window_size: int = ARCHIVED_STREAM_WINDOW
    ) -> AsyncIterator[JobResult]:
        """Replay only the newest archived window in chronological order."""
        decoder = MsgpackStreamDecoder()
        frames = await self._recent_archived_frames(job_id, limit=window_size)
        for frame in frames:
            for message in decoder.sse_decode(self._archive_payload(frame)):
                # A historical window is finite. Skip control markers but do
                # not terminate early: other lanes may have later output.
                if isinstance(message, SinapsisSentinel):
                    continue
                yield message

    async def cancel(self, job_id: str) -> AgentCancelResponse:
        """Cancel a job.

        Args:
            job_id: ID of the job to cancel.
        """
        response = await self._http.post(self._path(AGENT_PATHS.cancel, job_id=job_id))
        return AgentCancelResponse.model_validate(response)  # Return the response to indicate success or failure
