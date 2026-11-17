<h1 align="center">
<br>
<a href="https://sinapsis.tech/">
  <img
    src="https://github.com/SinapsisHub/brand-resources/blob/main/public/logo/sinapsis-logo-horizontal-dark-brand.png?raw=true"
    alt="Sinapsis"
    width="300">
</a>
<br>
sinapsis-sdk
<br>
</h1>

<h3 align="center">Typed Python clients for Sinapsis APIs.</h3>

`sinapsis-sdk` is the asynchronous Python client library for **Sinapsis Cloud** and the **Sinapsis Local API**. It provides typed resource methods for submitting Agents, managing executions, discovering Templates, and interacting with supported platform services without hand-building HTTP requests.

The SDK uses [`sinapsis-contracts`](../sinapsis-contracts/README.md) for shared request/response types and endpoint definitions, and the [`sinapsis`](../../core/sinapsis/README.md) Python interface for Agent and data models.

## Installation

Requires **Python 3.13+**. Install from the standard Python package index:

```bash
uv pip install sinapsis-sdk
# or
pip install sinapsis-sdk
```

For a project managed by `uv`, use `uv add sinapsis-sdk`.

## Choose a client

| Client | Import | Purpose |
| --- | --- | --- |
| `CloudSinapsisAPIClient` | `sinapsis_sdk.cloud_api.client` | Authenticated Cloud execution, saved Agents, schedules, Templates and platform resources. |
| `SinapsisAPIClient` | `sinapsis_sdk.local_api.client` | Execution and job control through a running Local API. |

Both clients are **asynchronous** and support `async with` for automatic HTTP connection cleanup. Call `await client.aclose()` if you do not use a context manager.

The Local API and Cloud are different execution backends. A method supported by one is not necessarily available on the other.

## Sinapsis Cloud

### Configure access

Set up a Cloud account and credentials using the Sinapsis CLI:

```bash
sinx-cloud configure
sinx-cloud profiles show cloud
```

Don't have an account? **[Visit sinapsis.tech to create one](https://sinapsis.tech/).**

The Cloud client uses your configured credentials. For API integrations, the SDK also supports scoped API-key authentication. Use an appropriate key scope for the operation being performed.

### Connect and discover Templates

```python
import asyncio

from sinapsis_sdk.cloud_api.client import CloudSinapsisAPIClient


async def main() -> None:
    async with CloudSinapsisAPIClient() as client:
        results = await client.templates.search("vision", limit=10)
        for template in results.items:
            print(template.get("class_name"), template.get("description"))


asyncio.run(main())
```

The default Cloud API endpoint is `https://api.sinapsis.tech/`. To use another deployment, pass an explicit configuration:

```python
from sinapsis_sdk.cloud_api.client import CloudSinapsisAPIClient
from sinapsis_sdk.cloud_api.cloud_config import CloudAPIConfig

client = CloudSinapsisAPIClient(
    CloudAPIConfig(api_url="https://api.sinapsis.tech/", timeout=30.0)
)
# Use the client inside async code and close it with await client.aclose().
```

### Cloud resource reference

Resources are accessed as attributes of `CloudSinapsisAPIClient`:

| Resource | Representative methods | What it does |
| --- | --- | --- |
| `client.jobs` | `submit`, `get_status`, `get_result`, `stream_results`, `cancel` | Submit a definition and inspect, stream or cancel its execution. |
| `client.agents` | `register`, `list`, `get`, `publish`, `versions`, `version`, `latest_version`, `all_versions` | Manage saved Agents and immutable versions. |
| `client.schedules` | `create`, `list`, `get`, `update`, `pause`, `resume`, `runs`, `delete` | Schedule an existing saved Agent version. |
| `client.templates` | `list`, `search`, `get`, `packages`, `search_registry` | Search available Templates and packages. |
| `client.files` | `upload`, `list`, `create`, `search`, `get`, `fetch`, `delete` | Work with Cloud files. |
| `client.secrets` | `create`, `list_user_secrets`, `get`, `delete` | Manage secret metadata and creation. |
| `client.api_keys` | `issue`, `generate`, `list_scoped`, `delete`, `validate` | Issue and manage scoped API keys. |
| `client.webhooks` | `register`, `list_user_webhooks`, `get`, `toggle`, `delete` | Manage webhook integrations. |

The SDK also exposes `archived_recent_results()` and `archived_stream_results()` on `client.jobs` for bounded historical result retrieval where supported by the Cloud API.

### Submit an Agent

A Cloud job can be submitted directly from an Agent definition; registration is not required for immediate execution.

```python
import asyncio
from pathlib import Path

import yaml
from sinapsis_sdk.cloud_api.client import CloudSinapsisAPIClient


async def main() -> None:
    definition = yaml.safe_load(Path("agent.yaml").read_text())

    async with CloudSinapsisAPIClient() as client:
        job = await client.jobs.submit(definition)
        print("Job ID:", job.job_id)

        status = await client.jobs.get_status(job.job_id)
        print("Status:", status.state)


asyncio.run(main())
```

`PyYAML` is used only to load the example file; install it separately if needed. `submit()` returns `AgentCreateResponse`. `get_status()` returns `AgentStatusResponse`.

For streaming, use `async for message in client.jobs.stream_results(job_id)`. The SDK decodes MessagePack output and filters control sentinels rather than exposing them as ordinary Agent results.

### Save and version Agents

```python
from sinapsis_sdk.cloud_api.client import CloudSinapsisAPIClient


async def save_and_publish(
    client: CloudSinapsisAPIClient,
    definition: dict,
    updated_definition: dict,
) -> None:
    registration = await client.agents.register(definition, version="v1")
    print(registration.agent_id, registration.agent_version_id)

    # A new definition creates a new immutable version.
    new_version = await client.agents.publish(
        registration.agent_id,
        updated_definition,
        version="v2",
    )
    print(new_version.id)
```

The `definition` and `updated_definition` variables are Agent-definition dictionaries supplied by the application. Version labels are required for both `register()` and `publish()`.

### Schedule a saved version

```python
from datetime import time

from sinapsis_contracts.cloud_api.models.saved_agent import AgentRegistration
from sinapsis_contracts.cloud_api.models.scheduling import ScheduleCreate, ScheduleType
from sinapsis_sdk.cloud_api.client import CloudSinapsisAPIClient


async def schedule_registered_agent(
    client: CloudSinapsisAPIClient,
    registration: AgentRegistration,
) -> None:
    schedule = ScheduleCreate(
        name="morning-report",
        agent_id=registration.agent_id,
        agent_version_id=registration.agent_version_id,
        schedule_type=ScheduleType.DAILY,
        local_time=time(9, 0),
        timezone="Europe/London",
    )

    created = await client.schedules.create(schedule)
    print(created.id, created.next_run_at)
```

A schedule refers to **one immutable Agent version**. Publishing another version does not change an existing schedule. For CLI scheduling commands, see [`Scheduling.md`](../../cli/sinapsis-cli/Scheduling.md).

### Scoped API keys

```python
from sinapsis_contracts.cloud_api.models.api_key_permissions import ApiKeyPermission
from sinapsis_sdk.cloud_api.client import CloudSinapsisAPIClient


async def issue_reporting_key(client: CloudSinapsisAPIClient) -> str:
    issued = await client.api_keys.issue(
        "reporting-service",
        scopes=[ApiKeyPermission.JOBS_READ.value],
    )
    # Store securely: the plaintext value is shown only on creation.
    return issued.api_key
```

Choose only the permissions needed by the integration. Listing keys returns metadata, not the original plaintext value.

## Sinapsis Local API

The local client communicates with a running [`sinapsis-api`](../../api/sinapsis-api/README.md) service. It does not run Agents within the SDK process.

```python
import asyncio

from sinapsis.agent import AgentSchema, generic_agent_schema_builder
from sinapsis_sdk.common.base_config import BaseAPIConfig
from sinapsis_sdk.local_api.client import SinapsisAPIClient


async def main(agent_definition: dict) -> None:
    schema: AgentSchema = generic_agent_schema_builder(agent_definition)

    async with SinapsisAPIClient(
        BaseAPIConfig(api_url="http://127.0.0.1:8005")
    ) as client:
        submitted = await client.jobs.submit(schema)
        status = await client.jobs.get_status(submitted.job_id)
        print(submitted.job_id, status.status)


# Call asyncio.run(main(your_agent_definition)) with an Agent dictionary.
```

| Local resource | Method | Return type / behaviour |
| --- | --- | --- |
| `client.jobs.submit(schema)` | Submit a validated `AgentSchema` | `StartJobResponse` |
| `client.jobs.get_status(job_id)` | Retrieve job state | `JobResponse` |
| `client.jobs.get_result(job_id)` | Read retained events | `list[LocalJobEvent]` |
| `client.jobs.stream_results(job_id, after=0)` | Stream decoded events | Async iterator of `LocalJobEvent` |
| `client.jobs.cancel(job_id)` | Request cancellation | `JobActionResponse` |
| `client.jobs.feedback(job_id, request)` | Respond to an approval request | `ApprovalResponse` |

`LocalJobEvent` preserves both the decoded `SSEEnvelope` (`event.envelope`) and its event-stream metadata (`event.metadata`, including the cursor). The Cloud job stream and the Local API event stream intentionally have different result shapes.

## Models, transport and errors

- **Agent graph validation** remains with `sinapsis.agent.generic_agent_schema_builder()`. The SDK transports Agent definitions; it does not replace the canonical graph validator.
- **Typed API contracts** live in `sinapsis-contracts`. Resources deserialize responses into Pydantic models where applicable.
- **HTTP errors** are represented by SDK exceptions such as `AuthenticationError`, `AuthorizationError`, `NotFoundError`, `APIError`, and `NetworkError` from `sinapsis_sdk.common.exceptions`.
- **Timeouts** are configured through `CloudAPIConfig` or `BaseAPIConfig`. Established streaming connections are handled separately from ordinary request timeouts.

```python
from sinapsis_sdk.common.exceptions import NotFoundError
from sinapsis_sdk.cloud_api.client import CloudSinapsisAPIClient


async def print_job_state(client: CloudSinapsisAPIClient, job_id: str) -> None:
    try:
        status = await client.jobs.get_status(job_id)
        print(status.state)
    except NotFoundError:
        print("Job not found or not accessible")
```

## Documentation and resources

- [Sinapsis documentation](https://docs.sinapsis.tech/)
- [Tutorials and examples](https://docs.sinapsis.tech/docs/latest/tutorials)
- [Sinapsis website](https://sinapsis.tech/)

## License

Sinapsis open-source components are available under your choice of the  [MIT License](LICENSE-MIT); or the [Apache License 2.0](LICENSE-APACHE) unless otherwise noted.
