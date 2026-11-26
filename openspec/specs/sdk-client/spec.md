# Python SDK and Contracts

## Purpose
`sinapsis-sdk` provides two async Python clients: `CloudSinapsisAPIClient` for Sinapsis Cloud and `SinapsisAPIClient` for the Local API. `sinapsis-contracts` holds the shared pydantic request and response models and the path constants, all under `/api/v1`. The SDK, the CLI and the Local API all use these contracts.

Unless otherwise noted, citations are relative to `packages/python/sdk/sinapsis-sdk/src/sinapsis_sdk/`. A `contracts:` prefix means `packages/python/sdk/sinapsis-contracts/src/sinapsis_contracts/`.

## Requirements

### Requirement: Cloud client resources
`CloudSinapsisAPIClient` SHALL expose async resources for `jobs`, `agents`, `schedules`, `files`, `api_keys`, `secrets`, `webhooks` and `templates`. It SHALL support `async with` and `aclose()`. (src: cloud_api/client.py:23-47)

#### Scenario: Context manager
- **WHEN** code runs `async with CloudSinapsisAPIClient() as c: await c.jobs.get_status(id)`
- **THEN** the HTTP client SHALL be closed when the block exits

### Requirement: Local client
`SinapsisAPIClient` SHALL expose only a `jobs` resource. (src: local_api/client.py:8-16)

#### Scenario: Local resources
- **WHEN** a `SinapsisAPIClient` is created
- **THEN** it SHALL have a `jobs` attribute and no cloud-only resources

### Requirement: Client configuration defaults
Each client SHALL take its base URL from a default that `SINAPSIS_API_URL` can override, and SHALL use a request timeout. (src: common/base_config.py:7-21; env_vars/sdk_env_vars.py:6-17)

#### Scenario: Defaults
- **WHEN** no configuration is given
- **THEN** the cloud base URL SHALL be `https://api.sinapsis.tech/`
- **AND** the local base URL SHALL be `http://localhost:8080/`
- **AND** the timeout SHALL be 30 s

### Requirement: Cloud authentication
The SDK SHALL authenticate with a stored API key if one exists, and otherwise with a session obtained from `POST /api/v1/auth/sdk/login {email, password}`. Every request SHALL send `Authorization: Bearer <token>`. (src: cloud_api/_auth.py:22-129; cloud_api/_http_client.py:35-46)

#### Scenario: Token near expiry
- **GIVEN** the access token expires in 30 s
- **WHEN** a request is made
- **THEN** the SDK SHALL refresh the session first via `POST /api/v1/auth/sdk/refresh`, since refresh happens 60 s before expiry under an asyncio lock
- **AND** it SHALL persist the rotated refresh token

#### Scenario: No credentials
- **WHEN** neither an API key nor a session is stored
- **THEN** "No credentials configured. Run 'sinapsis configure' first." SHALL be raised

### Requirement: Credential storage
Credentials SHALL be stored in the OS keyring under the service name `sinapsis-sdk` by default. (src: cloud_api/_credentials.py:13-165)

#### Scenario: File store opt-in
- **WHEN** `create_credential_store(use_file=True)` is used
- **THEN** credentials SHALL be written to `user_config_dir("sinapsis")/credentials.json` with mode 0600

### Requirement: Error taxonomy
The SDK SHALL map HTTP status codes and transport failures to `SinapsisError` subclasses, and SHALL NOT retry requests. (src: common/async_http_client.py:50-114; common/exceptions.py; common/exception_parser.py)

#### Scenario: Status mapping
- **WHEN** responses with error statuses are received
- **THEN** 401 SHALL raise `AuthenticationError`
- **AND** 403 SHALL raise `AuthorizationError`
- **AND** 404 SHALL raise `NotFoundError`
- **AND** any other error status SHALL raise `APIError(status_code, response)`
- **AND** an httpx transport error SHALL raise `NetworkError`

#### Scenario: Message extraction
- **WHEN** an error body is JSON
- **THEN** the message SHALL be taken from `message`, then `error`, then `detail`, falling back to the response text

### Requirement: Cloud job execution
Cloud `jobs` SHALL submit agent definitions to `POST /api/v1/agents` and return the `job_id`, and SHALL provide status, results, stream, cancel and archive operations. (src: cloud_api/resources/jobs.py:85-139; contracts: cloud_api/agents/state.py)

#### Scenario: Endpoints
- **WHEN** the job operations are called
- **THEN** status SHALL use `GET /agents/{job_id}?verbose`
- **AND** results SHALL use `GET /agents/{id}/results`, a msgpack SSE message
- **AND** stream SHALL use `GET /agents/{id}/stream`
- **AND** cancel SHALL use `POST /agents/{id}/cancel`
- **AND** archive SHALL use `GET /management/agent-results/{job_id}/archive?limit(1..200)&recent=true`
- **AND** job states SHALL be `QUEUED`, `PROCESSING`, `UPLOADING`, `COMPLETED`, `FAILED` or `CANCELLED`

#### Scenario: Stream until finished
- **WHEN** a client iterates `jobs.stream(job_id)`
- **THEN** iteration SHALL end on `AGENT_FINISHED` or `END_OF_STREAM`

### Requirement: Local job execution
Local `jobs.submit(AgentSchema)` SHALL POST the agent to `/api/v1/agents` and then POST `/api/v1/jobs` with a base64-serialized empty `DataContainer`. (src: local_api/resources/jobs.py:41-149)

#### Scenario: Submit locally
- **GIVEN** a Local API is running
- **WHEN** `jobs.submit(schema)` is called
- **THEN** the SDK SHALL make two HTTP calls and return the job id

#### Scenario: Results and streaming
- **WHEN** `get_result` is called
- **THEN** it SHALL replay the agent events with `after=0&job_id` and return only the first page
- **AND** `stream_results` SHALL currently fail with `AttributeError`, because it reads a `base_url` attribute that the HTTP wrapper does not have

### Requirement: Contract path rendering
Path constants SHALL be frozen dataclasses, and `BaseApiPaths.render` SHALL substitute `{name}` and `{name:path}` placeholders. The only versioning SHALL be the `/v1` segment. (src: contracts: common/paths/base.py:4-24)

#### Scenario: Render job path
- **WHEN** a jobs path template is rendered with `job_id="abc"`
- **THEN** `{job_id}` SHALL be replaced with `abc`
