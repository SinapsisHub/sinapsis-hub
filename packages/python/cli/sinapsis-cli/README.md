<h1 align="center">
<br>
<a href="https://sinapsis.tech/">
  <img
    src="https://github.com/SinapsisHub/brand-resources/blob/main/public/logo/sinapsis-logo-horizontal-dark-brand.png?raw=true"
    alt="Sinapsis"
    width="300">
</a>
<br>
Sinapsis CLI
<br>
</h1>

<p align="center">
Run Agents, inspect Templates, and manage local or Cloud workloads from your terminal.
</p>

<p align="center">
  <a href="#installation">Installation</a> ·
  <a href="#execution-profiles">Profiles</a> ·
  <a href="#running-agents">Jobs</a> ·
  <a href="#cloud-features">Cloud features</a> ·
  <a href="Scheduling.md">Scheduling</a> ·
  <a href="#shell-autocompletion">Autocompletion</a>
</p>

## Installation

**Python 3.13 or newer** is required. The CLI is published as `sinapsis-cli` and installs the `sinx`, `sinx-venv`, `sinx-api`, and `sinx-cloud` commands.

Install it as a standalone CLI with [uv](https://docs.astral.sh/uv/):

```bash
uv tool install sinapsis-cli
```

Or install it in a Python environment:

```bash
uv pip install sinapsis-cli
# or
pip install sinapsis-cli
```

No additional package index is needed for a standard installation.

```bash
sinx --help
```

## Execution profiles

Sinapsis CLI supports **three execution backends**. The commands you see depend on the selected profile.

| Profile | Entry point | What it does |
| --- | --- | --- |
| **Local Python** (`local`) | `sinx-venv` | Runs Agents directly with installed Python packages; inspects locally available Templates. |
| **Local API** (`local-api`) | `sinx-api` | Submits and manages jobs using a local Sinapsis API. |
| **Cloud** (`cloud`) | `sinx-cloud` | Runs Cloud jobs and manages saved Agents, Templates, files, integrations, and account resources. |

`sinx` uses your configured **default profile**, initially `local`. You can override it for an individual invocation:

```bash
sinx jobs run agent.yaml                     # Current default profile
sinx local jobs run agent.yaml               # Direct Python execution
sinx local-api jobs run agent.yaml           # Local API
sinx cloud jobs run agent.yaml               # Cloud API
```

The dedicated executables are shortcuts for those three built-in profiles:

```bash
sinx-venv jobs run agent.yaml
sinx-api jobs run agent.yaml
sinx-cloud jobs run agent.yaml
```

> Selecting or configuring `cloud` does **not** automatically change the default profile used by `sinx`.

### Configure a profile

```bash
# Configure only Cloud, including account sign-in
sinx-cloud configure

# Configure only the local API
sinx-api configure

# Configure only direct local execution
sinx-venv configure

# Interactive setup of all profiles and the default profile
sinx configure
```

**New to Sinapsis Cloud?** Visit **[sinapsis.tech](https://sinapsis.tech/)** to create an account before running `sinx-cloud configure`.

To inspect your current configuration:

```bash
sinx profiles list
sinx-cloud profiles show cloud
sinx profiles show local
sinx profiles show local-api
```

The built-in Cloud API URL is `https://api.sinapsis.tech` and the local API URL defaults to `http://localhost:8000`. `sinx-cloud profiles show cloud` displays the saved Cloud profile settings; it is not an authentication test.

### Choose a default or create another profile

```bash
sinx profiles default cloud
sinx profiles default local

# Create a second Cloud environment
sinx profiles create staging --backend cloud --api-url https://YOUR-API-HOST
sinx staging configure
sinx staging jobs list

# Choose an execution profile just for one terminal session
SINAPSIS_PROFILE=cloud sinx jobs list
```

Profiles can also be managed with `sinx profiles delete NAME` and inspected with `sinx profiles show NAME`. Run `sinx profiles --help` for the full profile command reference.

## Running Agents

Agent definitions are YAML files that connect reusable Templates. An example:

```yaml
agent:
  name: hello_world

templates:
  - template_name: Input
    class_name: InputTemplate
    attributes: {}

  - template_name: HelloWorld
    class_name: HelloWorld
    template_input: Input
    attributes:
      display_text: "Hello from Sinapsis!"
```

Install the Template packages required by your Agent in the environment where it runs. The example requires the corresponding `InputTemplate` and `HelloWorld` implementations.

### Local Python execution

Run directly in the selected Python environment:

```bash
sinx-venv jobs run agent.yaml
```

Local Python jobs execute directly; the CLI does **not** offer API-style `jobs status`, `jobs stream`, or `jobs cancel` commands for this backend.

### Local API and Cloud jobs

Both API-backed profiles support asynchronous job management:

```bash
# Submit a job
sinx-api jobs run agent.yaml
sinx-cloud jobs run agent.yaml

# Submit and follow the execution (either API-backed profile)
sinx-cloud jobs run agent.yaml --wait
sinx-cloud jobs run agent.yaml --stream

# Inspect a job
sinx-cloud jobs status JOB_ID
sinx-cloud jobs result JOB_ID
sinx-cloud jobs stream JOB_ID
sinx-cloud jobs cancel JOB_ID
```

The same `jobs status`, `jobs result`, `jobs stream`, and `jobs cancel` subcommands are available under `sinx-api` for local API jobs. An explicit `JOB_ID` can identify a job created elsewhere, subject to access permissions.

When a job ID is omitted, the CLI uses the most recent job remembered for the selected profile:

```bash
sinx-cloud jobs status
sinx-cloud jobs result
```

The following additional job options are available:

| Option | Availability | Effect |
| --- | --- | --- |
| `--wait` | Local API, Cloud | Wait for the job to finish and retrieve results. |
| `--stream` | Local API, Cloud | Stream execution output. |
| `--result` | Local API, Cloud | Request retained results after submission. |
| `--save-dir DIR` / `-o DIR` | Run, result, and stream commands where offered | Choose an output directory for saved artifacts (direct Python execution prints its result). |
| `--print-only` | All run commands; API results/stream | Print output rather than saving artifacts. |
| `--refresh` | Cloud `jobs result`, and `jobs run --result` | Retrieve a fresh result rather than a cached one. |
| `--verbose` / `-v` | Cloud `jobs status` | Include the full Agent definition. |

`--wait`, `--stream`, and `--result` are mutually exclusive when used with `jobs run`. For Cloud `jobs run`, `--refresh` requires `--result`.

### Job history

Every backend includes a local command history:

```bash
sinx-venv jobs list
sinx-api jobs list
sinx-cloud jobs list
sinx-cloud jobs list --all-profiles

# Clear the remembered jobs for one profile
sinx-cloud jobs clear
```

`jobs list` displays **jobs recorded by this CLI**; it is not a list of all jobs held by the Cloud service. Clearing local history does not cancel remote jobs.

## Discover Templates

### Templates installed locally

```bash
sinx-venv templates show-all
sinx-venv templates show-all --names-only
sinx-venv templates docstring TemplateName
sinx-venv templates example-config TemplateName
sinx-venv templates example-config TemplateName --output json
```

Template configuration examples support `pretty`, `json`, and `yaml` output formats.

### Templates available in Cloud

```bash
sinx-cloud templates list
sinx-cloud templates search "object detection"
sinx-cloud templates search "speech" --limit 20
sinx-cloud templates show TEMPLATE_UUID
sinx-cloud templates packages
```

Cloud search also supports `--package`, `--tag`, `--offset`, and `--limit` filters. The Cloud catalogue reflects the Templates and packages accessible to your account; it may differ from what is installed locally.

## Cloud features

Cloud adds commands for working with reusable Agents, assets, and integrations. Run `sinx-cloud <group> --help` to see all options.

### Saved Agents and immutable versions

```bash
sinx-cloud agents register agent.yaml --version v1
sinx-cloud agents list
sinx-cloud agents versions AGENT_UUID
sinx-cloud agents version AGENT_UUID VERSION_UUID
sinx-cloud agents publish AGENT_UUID updated-agent.yaml --version v2
```

`register` saves an Agent without executing it. `publish` creates a new immutable version. By default, `agents list` shows explicitly registered Agents; use `agents list --all` to include Agents saved through execution and earlier records.

Scheduling an existing Agent version is covered in **[Scheduling.md](Scheduling.md)**, including automatic version selection and recurring runs.

### Files

```bash
sinx-cloud files upload ./input.csv
sinx-cloud files list
sinx-cloud files search input.csv
sinx-cloud files get FILE_ID --output ./input.csv
sinx-cloud files fetch AGENT_ID FILE_ID --output ./artifact.bin
```

`get` retrieves a stored file by ID; `fetch` retrieves a file produced in an Agent's staging area.

### Secrets

```bash
sinx-cloud secrets create my-service-key   # Prompts securely for the value
sinx-cloud secrets list
sinx-cloud secrets get SECRET_UUID
sinx-cloud secrets delete SECRET_UUID
```

Use the interactive prompt to avoid passing secret values in shell history. `get` displays secret metadata, not the secret value.

### API keys

```bash
sinx-cloud api-keys permissions
sinx-cloud api-keys create --name my-integration --scope files:read --expire 7d
sinx-cloud api-keys list
sinx-cloud api-keys delete
```

The CLI supports scopes, expiry durations, and optional Agent restrictions. **Save new API key values when they are created**; they cannot be revealed later.

### Webhooks

```bash
sinx-cloud webhooks register --help
sinx-cloud webhooks list
sinx-cloud webhooks show WEBHOOK_UUID
sinx-cloud webhooks public-url WEBHOOK_UUID
sinx-cloud webhooks toggle WEBHOOK_UUID --inactive
sinx-cloud webhooks delete WEBHOOK_UUID
```

Webhook registration accepts an integration name, a provider, and optional credential and payload-schema settings.

### Package registry access

```bash
sinx-cloud packages indexes
sinx-cloud packages login
sinx-cloud packages logout
```

These commands help configure `uv` credentials for supported Sinapsis package indexes. Access to a registry may depend on your account and the registry's availability.

## CLI telemetry controls

CLI telemetry is optional and can be inspected or controlled directly:

```bash
sinx config telemetry status
sinx config telemetry preview
sinx config telemetry info
sinx config telemetry enable
sinx config telemetry history --limit 10
sinx config telemetry disable
sinx config telemetry disable --clear
```

> Telemetry is off unless enabled or explicitly overridden in the environment. `preview` lets you inspect an example of the information collected without storing or transmitting it.
> No personal information is ever collected. 

## Shell autocompletion

Install command, subcommand, and option completion for each executable you use:

```bash
sinx --install-completion
sinx-venv --install-completion
sinx-api --install-completion
sinx-cloud --install-completion
```

Restart your shell or reload its configuration after installation. Completion is installed separately for each executable.

## Resources

- [Sinapsis documentation](https://docs.sinapsis.tech/)
- [Tutorials and examples](https://docs.sinapsis.tech/docs/latest/tutorials)
- [Sinapsis website](https://sinapsis.tech/)
- [Scheduling and saved Agent versions](SCHEDULING.md)

## License

`sinapsis-cli` is dual-licensed under **MIT OR Apache-2.0**.