"""Single Router process for agent lifecycle, commands, journals, and streams."""

import asyncio
import sys
import uuid
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any

import zmq
import zmq.asyncio
from sinapsis.logging import sinapsis_logger

from sinapsis_api.constants import (
    ControlType,
    JobStatus,
    RouterError,
    StreamFrame,
    StreamOperation,
    WorkerFrame,
)
from sinapsis_api.env_vars import (
    SINAPSIS_API_AGENT_START_TIMEOUT_SECONDS,
    SINAPSIS_API_COMMAND_CACHE_SIZE,
    SINAPSIS_API_EVENT_MAX_BYTES,
    SINAPSIS_API_EVENT_MAX_BYTES_PER_AGENT,
    SINAPSIS_API_EVENT_MAX_EVENTS_PER_AGENT,
    SINAPSIS_API_EVENT_REPLAY_LIMIT,
    SINAPSIS_API_EVENT_REPLAY_MAX_BYTES,
    SINAPSIS_API_EVENT_RETENTION_SECONDS,
    SINAPSIS_API_JOURNAL_GC_INTERVAL_SECONDS,
    SINAPSIS_API_ROUTER_AGENT_ENDPOINT,
    SINAPSIS_API_ROUTER_API_ENDPOINT,
    SINAPSIS_API_ROUTER_STREAM_ENDPOINT,
    SINAPSIS_API_STOPPED_AGENT_RETENTION_SECONDS,
    SINAPSIS_API_SUBSCRIBER_QUEUE_SIZE,
    SINAPSIS_API_ZMQ_RECEIVE_HWM,
    SINAPSIS_API_ZMQ_SEND_HWM,
)
from sinapsis_api.journal import AgentEventJournals, ReplayResult
from sinapsis_api.models import AgentHandle, JobRecord
from sinapsis_api.protocol import EventRecord, pack_control, unpack_control


@dataclass(frozen=True, slots=True)
class RouterConfig:
    """Router configuration sourced from environment-backed constants."""

    api_endpoint: str = SINAPSIS_API_ROUTER_API_ENDPOINT
    agent_endpoint: str = SINAPSIS_API_ROUTER_AGENT_ENDPOINT
    stream_endpoint: str = SINAPSIS_API_ROUTER_STREAM_ENDPOINT
    retention_seconds: float = SINAPSIS_API_EVENT_RETENTION_SECONDS
    max_events_per_agent: int = SINAPSIS_API_EVENT_MAX_EVENTS_PER_AGENT
    max_bytes_per_agent: int = SINAPSIS_API_EVENT_MAX_BYTES_PER_AGENT
    max_event_bytes: int = SINAPSIS_API_EVENT_MAX_BYTES
    replay_limit: int = SINAPSIS_API_EVENT_REPLAY_LIMIT
    replay_max_bytes: int = SINAPSIS_API_EVENT_REPLAY_MAX_BYTES
    subscriber_queue_size: int = SINAPSIS_API_SUBSCRIBER_QUEUE_SIZE
    agent_start_timeout_seconds: float = SINAPSIS_API_AGENT_START_TIMEOUT_SECONDS
    stopped_agent_retention_seconds: float = SINAPSIS_API_STOPPED_AGENT_RETENTION_SECONDS
    journal_gc_interval_seconds: float = SINAPSIS_API_JOURNAL_GC_INTERVAL_SECONDS


class SinapsisAgentRouter:
    """Own all agent processes and stateless per-agent event streams."""

    def __init__(self, config: RouterConfig | None = None) -> None:
        self.config = config or RouterConfig()
        self.stream_id = str(uuid.uuid4())
        self.context = zmq.asyncio.Context.instance()
        self.journals = AgentEventJournals(
            stream_id=self.stream_id,
            retention_seconds=self.config.retention_seconds,
            max_events=self.config.max_events_per_agent,
            max_bytes=self.config.max_bytes_per_agent,
            max_event_bytes=self.config.max_event_bytes,
            stopped_agent_retention_seconds=self.config.stopped_agent_retention_seconds,
        )
        self.agents: dict[str, AgentHandle] = {}
        self.agent_by_identity: dict[bytes, AgentHandle] = {}
        self.jobs: dict[str, JobRecord] = {}
        self.command_results: OrderedDict[str, dict[str, Any]] = OrderedDict()
        self._background_tasks: set[asyncio.Task[Any]] = set()

    async def run(self) -> None:
        """Bind IPC sockets and serve until cancelled."""
        api_socket = self._router_socket(self.config.api_endpoint)
        agent_socket = self._router_socket(self.config.agent_endpoint)
        stream_socket = self._router_socket(self.config.stream_endpoint)
        sinapsis_logger.info("Router started with stream_id=%s.", self.stream_id)
        try:
            async with asyncio.TaskGroup() as task_group:
                task_group.create_task(self._api_loop(api_socket, agent_socket))
                task_group.create_task(self._agent_loop(agent_socket))
                task_group.create_task(self._stream_loop(stream_socket))
                task_group.create_task(self._process_watch_loop())
                task_group.create_task(self._journal_gc_loop())
        except Exception:
            sinapsis_logger.exception("Router stopped because of an unhandled exception.")
            raise
        finally:
            await self._terminate_agents()
            api_socket.close()
            agent_socket.close()
            stream_socket.close()

    def _router_socket(self, endpoint: str) -> zmq.asyncio.Socket:
        socket = self.context.socket(zmq.ROUTER)
        socket.setsockopt(zmq.LINGER, 0)
        socket.setsockopt(zmq.SNDHWM, SINAPSIS_API_ZMQ_SEND_HWM)
        socket.setsockopt(zmq.RCVHWM, SINAPSIS_API_ZMQ_RECEIVE_HWM)
        socket.bind(endpoint)
        return socket

    async def _api_loop(self, api_socket: zmq.asyncio.Socket, agent_socket: zmq.asyncio.Socket) -> None:
        while True:
            frames = await api_socket.recv_multipart(copy=False)
            identity = bytes(frames[0])
            try:
                response = await self._handle_api_request(unpack_control(frames[-1].buffer), agent_socket)
            except KeyError as exception:
                sinapsis_logger.warning("Router request referenced missing state: %s", exception)
                response = self._error(RouterError.NOT_FOUND, str(exception))
            except ValueError as exception:
                sinapsis_logger.warning("Router rejected request: %s", exception)
                response = self._error(RouterError.CONFLICT, str(exception))
            except Exception as exception:
                sinapsis_logger.exception("Router API request failed.")
                response = self._error(RouterError.INTERNAL, str(exception))
            await api_socket.send_multipart([identity, pack_control(response)])

    async def _handle_api_request(self, request: dict[str, Any], agent_socket: zmq.asyncio.Socket) -> dict[str, Any]:
        command_id = request.get("command_id")
        if command_id is not None and command_id in self.command_results:
            return self.command_results[command_id]

        control_type = ControlType(request["type"])
        if control_type == ControlType.HEALTH:
            result = {"ok": True, "status": "ready", "stream_id": self.stream_id}
        elif control_type == ControlType.LIST_AGENTS:
            result = {"ok": True, "agents": list(self.agents), "stream_id": self.stream_id}
        elif control_type == ControlType.START_AGENT:
            await self.start_agent(request["agent_id"], request["agent_definition"], agent_socket)
            result = {"ok": True, "stream_id": self.stream_id}
        elif control_type == ControlType.STOP_AGENT:
            await self.stop_agent(request["agent_id"], agent_socket)
            result = {"ok": True}
        elif control_type == ControlType.START_JOB:
            result = await self._start_job(request, agent_socket)
        elif control_type in {ControlType.CANCEL_JOB, ControlType.APPROVAL_RESPONSE}:
            await self._route_job_command(request, agent_socket)
            result = {"ok": True}
        elif control_type == ControlType.GET_JOB:
            job = self._require_job(request["job_id"])
            result = {"ok": True, "job": self._job_dict(job)}
        elif control_type == ControlType.EVENT_BOUNDS:
            window = await self.journals.bounds(request["agent_id"])
            result = {"ok": True, "window": self._window_dict(window)}
        else:
            sinapsis_logger.error("Unsupported control type: %s.", control_type.value)
            raise ValueError(f"Unsupported control type: {control_type.value}.")

        if command_id is not None:
            self._cache_command_result(command_id, result)
        return result

    async def _start_job(self, request: dict[str, Any], agent_socket: zmq.asyncio.Socket) -> dict[str, Any]:
        job_id = request["job_id"]
        agent_id = request["agent_id"]
        handle = self.agents.get(agent_id)
        if handle is None or not handle.ready.is_set():
            sinapsis_logger.error("Unknown or unready agent: %s.", agent_id)
            raise KeyError(f"Unknown or unready agent: {agent_id}.")
        if job_id in self.jobs:
            sinapsis_logger.error("Job already exists: %s.", job_id)
            raise ValueError(f"Job already exists: {job_id}.")
        self.jobs[job_id] = JobRecord(job_id, agent_id, handle.instance_id)
        await agent_socket.send_multipart([handle.identity, WorkerFrame.COMMAND.value, pack_control(request)])
        return {"ok": True, "job_id": job_id, "agent_id": agent_id}

    async def _route_job_command(self, request: dict[str, Any], agent_socket: zmq.asyncio.Socket) -> None:
        job = self._require_job(request["job_id"])
        handle = self.agents.get(job.agent_id)
        if handle is None:
            sinapsis_logger.error("Agent is not running: %s.", job.agent_id)
            raise RuntimeError(f"Agent is not running: {job.agent_id}.")
        await agent_socket.send_multipart([handle.identity, WorkerFrame.COMMAND.value, pack_control(request)])

    async def _agent_loop(self, agent_socket: zmq.asyncio.Socket) -> None:
        while True:
            frames = await agent_socket.recv_multipart(copy=False)
            identity = bytes(frames[0])
            frame_type = bytes(frames[1])
            if frame_type == WorkerFrame.HELLO.value:
                await self._register_worker(identity, unpack_control(frames[2].buffer), agent_socket)
                continue
            handle = self.agent_by_identity.get(identity)
            if handle is None:
                sinapsis_logger.warning("Ignoring frame from unknown worker identity.")
                continue
            if frame_type == WorkerFrame.READY.value:
                handle.ready.set()
            elif frame_type == WorkerFrame.EVENT.value:
                job_id_bytes = bytes(frames[2])
                try:
                    await self.journals.append(
                        agent_id=handle.agent_id,
                        instance_id=handle.instance_id,
                        job_id=job_id_bytes.decode() if job_id_bytes else None,
                        payload=bytes(frames[3].buffer),
                    )
                except ValueError:
                    sinapsis_logger.exception("Dropping oversized event from agent %s.", handle.agent_id)
            elif frame_type == WorkerFrame.JOB_STATE.value:
                state = unpack_control(frames[2].buffer)
                job = self.jobs.get(state["job_id"])
                if job is not None:
                    job.status = state["status"]
                    job.error = state.get("error")

    async def _register_worker(self, identity: bytes, hello: dict[str, Any], agent_socket: zmq.asyncio.Socket) -> None:
        handle = self.agents.get(hello["agent_id"])
        if handle is None or handle.instance_id != hello["instance_id"]:
            sinapsis_logger.warning("Ignoring stale worker registration for agent %s.", hello["agent_id"])
            return
        handle.identity = identity
        self.agent_by_identity[identity] = handle
        await agent_socket.send_multipart(
            [
                identity,
                WorkerFrame.COMMAND.value,
                pack_control({"type": ControlType.INIT.value, "agent_definition": handle.agent_definition}),
            ]
        )

    async def _stream_loop(self, stream_socket: zmq.asyncio.Socket) -> None:
        while True:
            frames = await stream_socket.recv_multipart(copy=False)
            identity = bytes(frames[0])
            operation = StreamOperation(bytes(frames[1]))
            parameters = unpack_control(frames[2].buffer)
            if operation == StreamOperation.REPLAY:
                self._track(asyncio.create_task(self._serve_replay(stream_socket, identity, parameters)))
            elif operation == StreamOperation.SUBSCRIBE:
                self._track(asyncio.create_task(self._serve_subscription(stream_socket, identity, parameters)))

    async def _serve_replay(self, socket: zmq.asyncio.Socket, identity: bytes, parameters: dict[str, Any]) -> None:
        try:
            replay = await self.journals.replay(
                agent_id=parameters["agent_id"],
                after=int(parameters.get("after", 0)),
                job_id=parameters.get("job_id"),
                limit=min(int(parameters.get("limit", self.config.replay_limit)), self.config.replay_limit),
                max_bytes=self.config.replay_max_bytes,
            )
            for record in replay.events:
                await self._send_event(socket, identity, record)
            await socket.send_multipart([identity, StreamFrame.DONE.value, pack_control(self._replay_dict(replay))])
        except Exception as exception:
            sinapsis_logger.exception("Event replay failed.")
            await socket.send_multipart(
                [
                    identity,
                    StreamFrame.DONE.value,
                    pack_control(self._error(RouterError.NOT_FOUND, str(exception))),
                ]
            )

    async def _serve_subscription(
        self, socket: zmq.asyncio.Socket, identity: bytes, parameters: dict[str, Any]
    ) -> None:
        agent_id = parameters["agent_id"]
        subscription_id: int | None = None
        try:
            subscription_id, replay, subscription = await self.journals.subscribe(
                agent_id=agent_id,
                after=parameters.get("after"),
                job_id=parameters.get("job_id"),
                queue_size=self.config.subscriber_queue_size,
                replay_limit=self.config.replay_limit,
                replay_max_bytes=self.config.replay_max_bytes,
            )
            if replay is not None:
                replay_boundary = subscription.after
                while True:
                    for record in replay.events:
                        await self._send_event(socket, identity, record)
                    if not replay.has_more:
                        break
                    replay = await self.journals.replay_through(
                        agent_id=agent_id,
                        after=replay.next_cursor,
                        through=replay_boundary,
                        job_id=parameters.get("job_id"),
                        limit=self.config.replay_limit,
                        max_bytes=self.config.replay_max_bytes,
                    )
            await socket.send_multipart(
                [
                    identity,
                    StreamFrame.LIVE.value,
                    pack_control({"stream_id": self.stream_id, "after": subscription.after}),
                ]
            )
            while not subscription.closed:
                record = await subscription.queue.get()
                await self._send_event(socket, identity, record)
            await socket.send_multipart(
                [
                    identity,
                    StreamFrame.LAGGED.value,
                    pack_control({"stream_id": self.stream_id, "resume_after": subscription.after}),
                ]
            )
        except Exception as exception:
            sinapsis_logger.exception("Live subscription failed for agent %s.", agent_id)
            await socket.send_multipart(
                [
                    identity,
                    StreamFrame.LAGGED.value,
                    pack_control(self._error(RouterError.NOT_FOUND, str(exception))),
                ]
            )
        finally:
            if subscription_id is not None:
                await self.journals.unsubscribe(agent_id, subscription_id)

    async def _send_event(self, socket: zmq.asyncio.Socket, identity: bytes, record: EventRecord) -> None:
        metadata, payload = record.zmq_frames()
        await socket.send_multipart([identity, StreamFrame.EVENT.value, metadata, payload], copy=False)

    async def start_agent(
        self, agent_id: str, agent_definition: dict[str, Any], agent_socket: zmq.asyncio.Socket
    ) -> None:
        """Start one isolated worker and preserve any existing logical-agent journal."""
        if agent_id in self.agents:
            sinapsis_logger.error("Agent already running: %s.", agent_id)
            raise ValueError(f"Agent already running: {agent_id}.")
        await self.journals.ensure_agent(agent_id)
        instance_id = str(uuid.uuid4())
        identity = f"agent:{agent_id}:{instance_id}".encode()
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            "-m",
            "sinapsis_api.agent_worker",
            "--endpoint",
            self.config.agent_endpoint,
            "--agent-id",
            agent_id,
            "--instance-id",
            instance_id,
        )
        handle = AgentHandle(agent_id, instance_id, process, identity, agent_definition)
        self.agents[agent_id] = handle
        self.agent_by_identity[identity] = handle
        try:
            await asyncio.wait_for(handle.ready.wait(), self.config.agent_start_timeout_seconds)
        except Exception:
            sinapsis_logger.exception("Agent %s failed to become ready.", agent_id)
            self.agents.pop(agent_id, None)
            self.agent_by_identity.pop(identity, None)
            await self.journals.mark_stopped(agent_id)
            if process.returncode is None:
                process.terminate()
            raise

    async def stop_agent(self, agent_id: str, agent_socket: zmq.asyncio.Socket) -> None:
        """Request worker shutdown without deleting retained event history."""
        handle = self.agents.get(agent_id)
        if handle is None:
            sinapsis_logger.error("Unknown running agent: %s.", agent_id)
            raise KeyError(f"Unknown running agent: {agent_id}.")
        await agent_socket.send_multipart(
            [
                handle.identity,
                WorkerFrame.COMMAND.value,
                pack_control({"type": ControlType.STOP.value}),
            ]
        )

    async def _process_watch_loop(self) -> None:
        while True:
            await asyncio.sleep(0.25)
            for agent_id, handle in tuple(self.agents.items()):
                if handle.process.returncode is None:
                    continue
                self.agents.pop(agent_id, None)
                self.agent_by_identity.pop(handle.identity, None)
                await self.journals.mark_stopped(agent_id)
                for job in self.jobs.values():
                    if (
                        job.agent_id == agent_id
                        and job.instance_id == handle.instance_id
                        and job.status
                        not in {
                            JobStatus.COMPLETED.value,
                            JobStatus.FAILED.value,
                            JobStatus.CANCELLED.value,
                        }
                    ):
                        job.status = JobStatus.FAILED.value
                        job.error = f"Agent process exited with code {handle.process.returncode}."
                sinapsis_logger.info("Agent %s process exited with code %s.", agent_id, handle.process.returncode)

    async def _journal_gc_loop(self) -> None:
        while True:
            await asyncio.sleep(self.config.journal_gc_interval_seconds)
            removed = await self.journals.purge_expired_stopped_agents()
            if removed:
                sinapsis_logger.info("Purged expired stopped-agent journals: %s", removed)

    async def _terminate_agents(self) -> None:
        for handle in tuple(self.agents.values()):
            if handle.process.returncode is None:
                handle.process.terminate()
        await asyncio.gather(*(handle.process.wait() for handle in self.agents.values()), return_exceptions=True)

    def _require_job(self, job_id: str) -> JobRecord:
        job = self.jobs.get(job_id)
        if job is None:
            sinapsis_logger.error("Unknown job: %s.", job_id)
            raise KeyError(f"Unknown job: {job_id}.")
        return job

    def _cache_command_result(self, command_id: str, result: dict[str, Any]) -> None:
        self.command_results[command_id] = result
        self.command_results.move_to_end(command_id)
        while len(self.command_results) > SINAPSIS_API_COMMAND_CACHE_SIZE:
            self.command_results.popitem(last=False)

    def _track(self, task: asyncio.Task[Any]) -> None:
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

    @staticmethod
    def _error(error: RouterError, detail: str) -> dict[str, Any]:
        return {"ok": False, "error": error.value, "detail": detail}

    @staticmethod
    def _job_dict(job: JobRecord) -> dict[str, Any]:
        return {
            "job_id": job.job_id,
            "agent_id": job.agent_id,
            "instance_id": job.instance_id,
            "status": job.status,
            "error": job.error,
        }

    @staticmethod
    def _window_dict(window: Any) -> dict[str, Any]:
        return {
            "stream_id": window.stream_id,
            "agent_id": window.agent_id,
            "oldest_cursor": window.oldest_cursor,
            "latest_cursor": window.latest_cursor,
            "event_count": window.event_count,
            "size_bytes": window.size_bytes,
        }

    def _replay_dict(self, replay: ReplayResult) -> dict[str, Any]:
        return {
            "ok": True,
            "stream_id": replay.window.stream_id,
            "agent_id": replay.window.agent_id,
            "requested_after": replay.requested_after,
            "effective_after": replay.effective_after,
            "oldest_cursor": replay.window.oldest_cursor,
            "latest_cursor": replay.window.latest_cursor,
            "next_cursor": replay.next_cursor,
            "truncated": replay.truncated,
            "has_more": replay.has_more,
            "event_count": len(replay.events),
        }


async def main() -> None:
    """Run the Router process."""
    await SinapsisAgentRouter().run()


if __name__ == "__main__":
    asyncio.run(main())
