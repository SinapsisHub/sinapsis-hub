# Local API (sinapsis-api)

## Purpose
`sinapsis-api` is "Sinapsis Local API", a self-hosted FastAPI service. It runs Agents as long-lived worker processes and exposes job submission and replayable event streams. The service has three parts:
- Stateless FastAPI workers.
- A single ZeroMQ **Router** process that holds all job and journal state in memory.
- One **agent worker** subprocess per Agent (`python -m sinapsis_api.agent_worker`).

API workers talk to the Router over ZeroMQ DEALER sockets with msgpack control messages. There is no authentication and no CORS middleware.

Citations are relative to `packages/python/api/sinapsis-api/src/sinapsis_api/` unless noted.

## Requirements

### Requirement: Health route
The service SHALL expose `GET /api/v1/health`, which returns `{status: "ready", stream_id}`. (src: api/routes/health.py:14-18)

#### Scenario: Health check
- **WHEN** a client calls `GET /api/v1/health`
- **THEN** the response SHALL be 200 with `status: "ready"`

### Requirement: Agent start and stop routes
`POST /api/v1/agents` SHALL accept an `AgentSchema`, assign a uuid4 `agent_id` when one is missing, and return 201 with `{agent_id, status: "running", stream_id}`. `DELETE /api/v1/agents/{agent_id}` SHALL return `{status: "stopped"}`. (src: api/routes/agents.py:26-50)

#### Scenario: Start agent without id
- **WHEN** a client POSTs an agent definition that has no `agent_id`
- **THEN** the response SHALL be 201
- **AND** it SHALL include a generated uuid4 `agent_id` and `status: "running"`

#### Scenario: Stop agent
- **WHEN** a client calls `DELETE /api/v1/agents/{agent_id}`
- **THEN** the response SHALL include `status: "stopped"`

### Requirement: List agents route
The service SHALL expose a GET route that returns `AgentsResponse{agents[], stream_id}`. The route is currently registered at `/api/v1/agents/api/v1/agents`, because the router prefix and the route path are both `/api/v1/agents`. (src: api/routes/agents.py:23,53)

#### Scenario: Doubled path
- **WHEN** a client calls `GET /api/v1/agents/api/v1/agents`
- **THEN** the list of running agents SHALL be returned
- **AND** `GET /api/v1/agents` SHALL NOT be routed to this handler

### Requirement: Job routes
The service SHALL expose these job routes:
- `POST /api/v1/jobs`: accepts `{agent_id, job_id?, payload?}`, where `payload` is a base64 DataContainer.
- `GET /api/v1/jobs/{job_id}`
- `POST /api/v1/jobs/{job_id}/cancel`
- `POST /api/v1/jobs/{job_id}/feedback`: human-in-the-loop approval.

(src: api/routes/jobs.py:29-74; api/routes/_common.py:43-52)

#### Scenario: Submit job
- **WHEN** a client POSTs `{agent_id}` to `/api/v1/jobs`
- **THEN** the response SHALL be 202 with `{job_id, agent_id, status: "queued"}`

#### Scenario: Bad payload encoding
- **WHEN** the `payload` is not valid base64
- **THEN** the response SHALL be 422 with "payload must be valid base64"

#### Scenario: Job status
- **WHEN** a client calls `GET /api/v1/jobs/{job_id}`
- **THEN** the response SHALL include `job_id`, `agent_id`, `instance_id`, `status` and `error`

#### Scenario: Cancel and feedback
- **WHEN** a client POSTs to `/cancel`
- **THEN** the response SHALL be 202 with `{job_id, accepted: true}`
- **AND** POSTing `{request_id, approved}` to `/feedback` SHALL return 202 with `accepted: true`

### Requirement: Event stream routes
The service SHALL expose two ways to read agent events, plus a per-job WebSocket:
- An HTTP replay at `GET /api/v1/agents/{agent_id}/events?after&job_id&limit`.
- A WebSocket at `/api/v1/agents/{agent_id}/events/ws?after&job_id`.
- A job WebSocket at `/api/v1/jobs/{job_id}//events?after`. The double slash is part of the contract path.

(src: api/routes/agents.py:60-84; api/routes/jobs.py:77-81; packages/python/sdk/sinapsis-contracts/src/sinapsis_contracts/local_api/paths/jobs.py:13)

#### Scenario: HTTP replay format
- **WHEN** a client calls the replay route
- **THEN** the body SHALL be `application/x-sinapsis-events` length-prefixed frames
- **AND** `limit` SHALL default to 1000 and be bounded to 1..REPLAY_LIMIT

#### Scenario: WebSocket frame format
- **WHEN** an event is pushed over a WebSocket
- **THEN** the frame SHALL be `msgpack(metadata)` followed by SSEEnvelope bytes

#### Scenario: Stream failure
- **WHEN** the event stream fails internally
- **THEN** the WebSocket SHALL close with code 1011 and "event stream failed"

### Requirement: Error mapping
The service SHALL map Router error codes to HTTP status codes: `not_found` (from `KeyError`) to 404, `conflict` (from `ValueError`) to 409, `unavailable` to 503, and any other code to 500. (src: api/routes/_common.py:22-40; agent_router.py:121-129)

#### Scenario: Unknown agent
- **WHEN** a job is started for an unknown agent
- **THEN** the response SHALL be 404

#### Scenario: Duplicate job or running agent
- **WHEN** a job is started twice with the same `job_id`, or an agent that is already running is started
- **THEN** the response SHALL be 409

#### Scenario: Agent start timeout
- **WHEN** an agent is not ready within `SINAPSIS_API_AGENT_START_TIMEOUT_SECONDS` (default 15)
- **THEN** the response SHALL be 500

#### Scenario: Cancel when process is gone
- **WHEN** a job is cancelled after its agent process has exited
- **THEN** a `RuntimeError` SHALL surface as 500

#### Scenario: Replay for an unknown agent
- **WHEN** events are replayed for an unknown agent
- **THEN** an unhandled `RuntimeError` SHALL currently produce 500

### Requirement: Job lifecycle
A job SHALL move from `queued` to `running`, and then to one of `completed`, `failed` or `cancelled`. (src: constants.py:40-45; agent_worker.py:181-203)

#### Scenario: Successful job
- **WHEN** a queued job runs to completion
- **THEN** its status SHALL go from `queued` to `running` to `completed`

### Requirement: Agent execution modes
An agent worker SHALL run the Agent according to its mode:
- `SINGLE`: emit one result per job.
- `GENERATOR`: emit one result for each yielded item.
- `LOOP_FOREVER`: run as a production task immediately after INIT.

(src: onexth_runtime.py:20-68)

#### Scenario: Generator agent
- **GIVEN** a GENERATOR agent that yields 3 items
- **WHEN** a job runs
- **THEN** 3 result events SHALL be emitted

#### Scenario: Finite job on loop-forever agent
- **GIVEN** a LOOP_FOREVER agent
- **WHEN** a finite job is submitted to it
- **THEN** a `ValueError` SHALL be raised, which maps to a conflict

### Requirement: Worker crash handling
The Router SHALL poll agent processes every 0.25 s. When a process exits, the Router SHALL mark all of that agent's non-terminal jobs as `failed`. (src: agent_router.py:381-403)

#### Scenario: Worker crash
- **GIVEN** a running job
- **WHEN** its agent process exits with code 137
- **THEN** the job SHALL be `failed` with the error "Agent process exited with code 137."

### Requirement: Event journal retention
Each agent SHALL have a journal ring with monotonic cursors that start at 1. The journal SHALL be pruned by age, by event count and by bytes. (src: journal.py:62-154)

#### Scenario: Retention defaults
- **WHEN** no journal env vars are set
- **THEN** `SINAPSIS_API_EVENT_RETENTION_SECONDS` SHALL be 3600
- **AND** `SINAPSIS_API_EVENT_MAX_EVENTS_PER_AGENT` SHALL be 10000
- **AND** `SINAPSIS_API_EVENT_MAX_BYTES_PER_AGENT` SHALL be 256 MiB
- **AND** `SINAPSIS_API_EVENT_MAX_BYTES` SHALL be 100 MiB, and larger events SHALL be dropped
- **AND** `SINAPSIS_API_EVENT_REPLAY_MAX_BYTES` SHALL be 64 MiB

#### Scenario: Expired cursor
- **WHEN** a replay requests a cursor older than the retained window
- **THEN** the cursor SHALL be clamped to the window
- **AND** the response SHALL report `truncated=true`

### Requirement: Replay headers
Replay responses SHALL include these headers: `X-Sinapsis-Stream-Id`, `X-Sinapsis-Oldest-Cursor`, `X-Sinapsis-Latest-Cursor`, `X-Sinapsis-Next-Cursor`, `X-Sinapsis-Truncated` and `X-Sinapsis-Has-More`. (src: api/routes/agents.py:71-78; packages/python/sdk/sinapsis-contracts/src/sinapsis_contracts/common/constants/__init__.py:5-14)

#### Scenario: Paging
- **GIVEN** a journal with more events than `limit`
- **WHEN** a replay is requested
- **THEN** `X-Sinapsis-Has-More` SHALL be true
- **AND** `X-Sinapsis-Next-Cursor` SHALL identify where the next page starts

### Requirement: Live subscription semantics
A WebSocket opened without `after` SHALL receive only live events. A WebSocket opened with `after=0` SHALL replay the journal first and then follow live events. A subscriber whose queue overflows SHALL be closed. (src: journal.py:191-298; api/routes/_common.py:66-85)

#### Scenario: Lagging subscriber
- **GIVEN** `SINAPSIS_API_SUBSCRIBER_QUEUE_SIZE` is at its default of 1024
- **WHEN** a subscriber's queue overflows
- **THEN** the socket SHALL close with code 4008 and "subscriber lagged; reconnect using the last processed cursor"

#### Scenario: Reconnect after lag
- **WHEN** the subscriber reconnects with `after=<last processed cursor>`
- **THEN** it SHALL receive every retained event after that cursor

### Requirement: Idempotent control commands
Each control request to the Router SHALL carry a uuid4 `command_id`. The Router SHALL cache up to `SINAPSIS_API_COMMAND_CACHE_SIZE` results (default 10000). (src: api/routes/_common.py:17-19; agent_router.py:133-135,425-429)

#### Scenario: Retried command
- **WHEN** the same `command_id` is received twice
- **THEN** the cached result SHALL be returned
- **AND** the command SHALL NOT be executed again

### Requirement: Network configuration
The API SHALL listen on `SINAPSIS_API_HOST_PORT` and SHALL reach the Router through the ZeroMQ endpoints given by the env vars. (src: env_vars/env_vars.py)

#### Scenario: Defaults
- **WHEN** no env vars are set
- **THEN** `SINAPSIS_API_HOST_PORT` SHALL be 8000
- **AND** the Router API, agent and stream endpoints SHALL be `tcp://127.0.0.1:8765`, `:8766` and `:8767`
- **AND** `SINAPSIS_API_ZMQ_SEND_HWM` and `SINAPSIS_API_ZMQ_RECEIVE_HWM` SHALL be 1024
- **AND** `SINAPSIS_API_WORKER_OUTBOUND_QUEUE_SIZE` SHALL be 1024
- **AND** `SINAPSIS_API_STOPPED_AGENT_RETENTION_SECONDS` SHALL be 86400
- **AND** `SINAPSIS_API_JOURNAL_GC_INTERVAL_SECONDS` SHALL be 30
- **AND** `SINAPSIS_PACKAGE_INDEX` SHALL be `https://pypi.sinapsis.ai`

### Requirement: Container deployment
The service SHALL ship a Docker image based on `python:3.13-slim` and a compose file. The compose file publishes port 8005. Its router service currently runs the module `sinapsis_api.router`, which does not exist; the real module is `agent_router`. (src: packages/python/api/sinapsis-api/docker/Dockerfile; docker/api-compose.yaml:7-57)

#### Scenario: Compose port
- **WHEN** the stack is started with the shipped compose file
- **THEN** the API SHALL be published on host port 8005
