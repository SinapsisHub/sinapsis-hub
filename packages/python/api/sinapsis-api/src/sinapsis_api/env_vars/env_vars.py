from pydantic import BaseModel
from sinapsis.env_vars import EnvVarEntry


class _SinapsisAPIEnvVars(BaseModel):
    """Environment variable definitions for the Sinapsis API."""

    SINAPSIS_PACKAGE_INDEX: EnvVarEntry = EnvVarEntry(
        var_name="SINAPSIS_PACKAGE_INDEX",
        default_value="https://pypi.sinapsis.ai",
        description="Additional package index where sinapsis packages may live other than in the public pypi registry.",
        return_type=str,
    )

    SINAPSIS_API_HOST_PORT: EnvVarEntry = EnvVarEntry(
        var_name="SINAPSIS_API_HOST_PORT",
        default_value="8000",
        description="The host port of the Sinapsis API",
        return_type=int,
    )

    SINAPSIS_API_ROUTER_API_ENDPOINT: EnvVarEntry = EnvVarEntry(
        var_name="SINAPSIS_API_ROUTER_API_ENDPOINT",
        default_value="tcp://127.0.0.1:8765",
        description=(
            "ZeroMQ endpoint exposed by the Router for API worker communication. "
            "API processes use this endpoint to send commands to the Router and "
            "receive command responses."
        ),
        return_type=str,
    )

    SINAPSIS_API_ROUTER_AGENT_ENDPOINT: EnvVarEntry = EnvVarEntry(
        var_name="SINAPSIS_API_ROUTER_AGENT_ENDPOINT",
        default_value="tcp://127.0.0.1:8766",
        description=(
            "ZeroMQ endpoint exposed by the Router for agent worker communication. "
            "Agent subprocesses use this endpoint for commands, lifecycle messages, "
            "and event delivery to the Router."
        ),
        return_type=str,
    )

    SINAPSIS_API_ROUTER_STREAM_ENDPOINT: EnvVarEntry = EnvVarEntry(
        var_name="SINAPSIS_API_ROUTER_STREAM_ENDPOINT",
        default_value="tcp://127.0.0.1:8767",
        description=(
            "ZeroMQ endpoint exposed by the Router for event-stream subscribers. "
            "API workers use this endpoint to request retained event replay and "
            "subscribe to live agent events."
        ),
        return_type=str,
    )

    SINAPSIS_API_EVENT_RETENTION_SECONDS: EnvVarEntry = EnvVarEntry(
        var_name="SINAPSIS_API_EVENT_RETENTION_SECONDS",
        default_value=3600.0,
        description=(
            "Maximum age, in seconds, of events retained in each agent's rolling "
            "journal. Events older than this value are eligible for eviction."
        ),
        return_type=float,
    )

    SINAPSIS_API_EVENT_MAX_EVENTS_PER_AGENT: EnvVarEntry = EnvVarEntry(
        var_name="SINAPSIS_API_EVENT_MAX_EVENTS_PER_AGENT",
        default_value=10_000,
        description=(
            "Maximum number of events retained in a single agent's rolling journal. "
            "When the limit is exceeded, the oldest retained events are evicted."
        ),
        return_type=int,
    )

    SINAPSIS_API_EVENT_MAX_BYTES_PER_AGENT: EnvVarEntry = EnvVarEntry(
        var_name="SINAPSIS_API_EVENT_MAX_BYTES_PER_AGENT",
        default_value=256 * 1024 * 1024,
        description=(
            "Maximum cumulative size, in bytes, of serialized event payloads retained "
            "in a single agent's rolling journal. The oldest events are evicted when "
            "the journal exceeds this limit."
        ),
        return_type=int,
    )

    SINAPSIS_API_EVENT_MAX_BYTES: EnvVarEntry = EnvVarEntry(
        var_name="SINAPSIS_API_EVENT_MAX_BYTES",
        default_value=100 * 1024 * 1024,
        description=(
            "Maximum serialized payload size, in bytes, accepted for an individual "
            "agent event. Events exceeding this limit are rejected instead of being "
            "added to the agent journal."
        ),
        return_type=int,
    )

    SINAPSIS_API_EVENT_REPLAY_LIMIT: EnvVarEntry = EnvVarEntry(
        var_name="SINAPSIS_API_EVENT_REPLAY_LIMIT",
        default_value=1000,
        description=(
            "Maximum number of retained events returned in a single replay page. "
            "Larger replays are paginated and continue from the last returned cursor."
        ),
        return_type=int,
    )

    SINAPSIS_API_EVENT_REPLAY_MAX_BYTES: EnvVarEntry = EnvVarEntry(
        var_name="SINAPSIS_API_EVENT_REPLAY_MAX_BYTES",
        default_value=64 * 1024 * 1024,
        description=(
            "Maximum cumulative serialized payload size, in bytes, returned in a "
            "single event replay page. Replay continues on a subsequent page when "
            "additional retained events remain."
        ),
        return_type=int,
    )

    SINAPSIS_API_SUBSCRIBER_QUEUE_SIZE: EnvVarEntry = EnvVarEntry(
        var_name="SINAPSIS_API_SUBSCRIBER_QUEUE_SIZE",
        default_value=1024,
        description=(
            "Maximum number of live events buffered for an individual event "
            "subscriber. A subscriber that cannot consume events before this queue "
            "fills is treated as lagging without blocking other subscribers."
        ),
        return_type=int,
    )

    SINAPSIS_API_AGENT_START_TIMEOUT_SECONDS: EnvVarEntry = EnvVarEntry(
        var_name="SINAPSIS_API_AGENT_START_TIMEOUT_SECONDS",
        default_value=15.0,
        description=(
            "Maximum time, in seconds, the Router waits for a newly spawned agent "
            "subprocess to report that it is ready before considering startup failed."
        ),
        return_type=float,
    )

    SINAPSIS_API_STOPPED_AGENT_RETENTION_SECONDS: EnvVarEntry = EnvVarEntry(
        var_name="SINAPSIS_API_STOPPED_AGENT_RETENTION_SECONDS",
        default_value=86_400.0,
        description=(
            "Maximum time, in seconds, to retain a stopped agent's journal and "
            "associated Router state. This allows retained events to remain available "
            "for replay after the agent process has exited."
        ),
        return_type=float,
    )

    SINAPSIS_API_JOURNAL_GC_INTERVAL_SECONDS: EnvVarEntry = EnvVarEntry(
        var_name="SINAPSIS_API_JOURNAL_GC_INTERVAL_SECONDS",
        default_value=30.0,
        description=(
            "Interval, in seconds, between Router garbage-collection passes that "
            "remove expired event data and purge stopped-agent journals whose "
            "retention period has elapsed."
        ),
        return_type=float,
    )

    SINAPSIS_API_WORKER_OUTBOUND_QUEUE_SIZE: EnvVarEntry = EnvVarEntry(
        var_name="SINAPSIS_API_WORKER_OUTBOUND_QUEUE_SIZE",
        default_value=1024,
        description=(
            "Maximum number of outbound event and control messages buffered inside "
            "an agent subprocess while waiting to send them to the Router. The shared "
            "FIFO queue preserves event and job-state ordering."
        ),
        return_type=int,
    )

    SINAPSIS_API_COMMAND_CACHE_SIZE: EnvVarEntry = EnvVarEntry(
        var_name="SINAPSIS_API_COMMAND_CACHE_SIZE",
        default_value=10_000,
        description=(
            "Maximum number of processed command identifiers retained by the Router "
            "for command deduplication and idempotent command handling."
        ),
        return_type=int,
    )

    SINAPSIS_API_ZMQ_SEND_HWM: EnvVarEntry = EnvVarEntry(
        var_name="SINAPSIS_API_ZMQ_SEND_HWM",
        default_value=1024,
        description=(
            "ZeroMQ send high-water mark used by Sinapsis API IPC sockets. It limits "
            "the number of outbound messages ZeroMQ may queue before applying "
            "backpressure."
        ),
        return_type=int,
    )

    SINAPSIS_API_ZMQ_RECEIVE_HWM: EnvVarEntry = EnvVarEntry(
        var_name="SINAPSIS_API_ZMQ_RECEIVE_HWM",
        default_value=1024,
        description=(
            "ZeroMQ receive high-water mark used by Sinapsis API IPC sockets. It "
            "limits the number of inbound messages ZeroMQ may queue for a socket "
            "before applying its configured queueing behavior."
        ),
        return_type=int,
    )
