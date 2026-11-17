"""Shared protocol and lifecycle constants."""

from enum import Enum


class ControlType(str, Enum):
    HEALTH = "health"
    LIST_AGENTS = "list_agents"
    START_AGENT = "start_agent"
    STOP_AGENT = "stop_agent"
    START_JOB = "start_job"
    CANCEL_JOB = "cancel_job"
    APPROVAL_RESPONSE = "approval_response"
    GET_JOB = "get_job"
    EVENT_BOUNDS = "event_bounds"
    INIT = "init"
    STOP = "stop"


class WorkerFrame(bytes, Enum):
    HELLO = b"HELLO"
    COMMAND = b"COMMAND"
    READY = b"READY"
    EVENT = b"EVENT"
    JOB_STATE = b"JOB_STATE"


class StreamOperation(bytes, Enum):
    REPLAY = b"REPLAY"
    SUBSCRIBE = b"SUBSCRIBE"


class StreamFrame(bytes, Enum):
    EVENT = b"EVENT"
    DONE = b"DONE"
    LIVE = b"LIVE"
    LAGGED = b"LAGGED"


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentStatus(str, Enum):
    RUNNING = "running"
    STOPPED = "stopped"


class RouterError(str, Enum):
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    UNAVAILABLE = "unavailable"
    INTERNAL = "internal"
