# CLI Job Execution

## Purpose
`sinx jobs` runs an Agent YAML and retrieves its results. Where it runs depends on the profile's backend:
- **local-venv**: in-process, in the current interpreter
- **local-api**: on the Sinapsis Local API
- **cloud**: on Sinapsis Cloud

`sinx templates` (local-venv) inspects the Templates installed in the current environment.

Citations below are relative to `packages/python/cli/sinapsis-cli/src/sinapsis_cli/`.

## Requirements

### Requirement: Local-venv job run
`sinx [local] jobs run AGENT_YAML` SHALL build the Agent with `sinapsis.cli.generic_agent_builder`, execute it in the current Python interpreter, and print the result. (src: commands/local_venv/jobs.py:31-76)

#### Scenario: Run hello world locally
- **GIVEN** an agent YAML chaining InputTemplate → HelloWorld
- **WHEN** a user runs `sinx jobs run agent_config.yml`
- **THEN** the agent SHALL execute in-process
- **AND** the resulting container SHALL be printed

#### Scenario: Current limitations
- **WHEN** `--save-dir` or `--print-only` is passed on local-venv
- **THEN** the option SHALL be accepted but currently has no effect
- **AND** the profile's `venv` setting SHALL NOT be used for execution
- **AND** the job SHALL NOT be recorded in the job history

### Requirement: Template introspection
On the local-venv backend, `sinx templates` SHALL provide `show-all [--names-only]`, `docstring NAME` and `example-config NAME [--output pretty|json|yaml]`, and these SHALL operate on the Templates discoverable in the environment. (src: commands/local_venv/templates.py; _templates_render.py:44-56)

#### Scenario: Example config
- **WHEN** a user runs `sinx templates example-config HelloWorld`
- **THEN** a YAML agent snippet listing HelloWorld's attributes and their defaults SHALL be printed
- **AND** the output format SHALL default to `yaml`

#### Scenario: Names-only exit code
- **WHEN** a user runs `sinx templates show-all --names-only`
- **THEN** the template names SHALL be printed
- **AND** the command currently exits with code 1 even though the listing succeeded

### Requirement: Remote job submission
On the local-api and cloud backends, `jobs run AGENT_YAML` SHALL submit the agent, print `Job ID: {id}`, and record the job in the profile's history. (src: commands/local_api/jobs.py:26-156; commands/cloud/jobs.py:34-82)

#### Scenario: Local API submission
- **WHEN** a job is run on a local-api profile
- **THEN** the definition SHALL be built with `generic_agent_schema_builder`
- **AND** it SHALL be sent as POST `/api/v1/agents` followed by POST `/api/v1/jobs`

#### Scenario: Cloud submission
- **WHEN** a job is run on a cloud profile
- **THEN** the raw YAML dict SHALL be sent as the agent definition

### Requirement: Run follow modes
`jobs run` SHALL accept at most one of `--wait`, `--result` and `--stream`. (src: commands/local_api/jobs.py:18-198; commands/cloud/jobs.py:207-437)

#### Scenario: Conflicting flags
- **WHEN** a user runs `sinx cloud jobs run a.yml --wait --stream`
- **THEN** the CLI SHALL print "Options --wait, --result, and --stream are mutually exclusive." and exit with code 1

#### Scenario: Wait on local API
- **WHEN** `--wait` is used on a local-api profile
- **THEN** the CLI SHALL poll every 0.25 s, with no timeout, until the status is completed, failed or cancelled
- **AND** it SHALL then fetch the results unless the status is failed

#### Scenario: Wait on cloud
- **WHEN** `--wait` is used on a cloud profile
- **THEN** the CLI SHALL poll every 1.0 s, with no timeout
- **AND** it SHALL treat done, completed, complete, failed, error, cancelled and canceled (case-insensitive) as terminal states

#### Scenario: Stream on local API
- **WHEN** `--stream` is used on a local-api profile
- **THEN** the CLI SHALL request the job status after each received event

### Requirement: Job follow-up commands
On the local-api and cloud backends, `jobs` SHALL provide `status`, `result`, `stream`, `cancel`, `list` and `clear`, and SHALL use the profile's last job when no JOB_ID is given. (src: commands/local_api/jobs.py:200-255; shared/jobs.py)

#### Scenario: Cancel last job
- **GIVEN** a running job on profile `local-api`
- **WHEN** a user runs `sinx local-api jobs cancel`
- **THEN** cancellation SHALL be requested
- **AND** the CLI SHALL print "Cancelled job <id>."

#### Scenario: Status output
- **WHEN** a user runs `jobs status`
- **THEN** the CLI SHALL print Job ID, State, Agent, Instance and Error lines

### Requirement: Cloud result recovery from archive
When live cloud results are unavailable, `jobs result` and `jobs stream` SHALL fall back to the database archive of result frames. (src: commands/cloud/jobs.py:229-337)

#### Scenario: Expired live state
- **GIVEN** a finished cloud job whose Redis state has expired (`NotFoundError`, or 503 "Job state unavailable"; streaming also accepts 410)
- **WHEN** a user runs `sinx cloud jobs result <id>`
- **THEN** the CLI SHALL replay the archived frames
- **AND** it SHALL print "Recovered N recent result frame(s) from the database archive."

#### Scenario: Nothing recoverable
- **WHEN** neither Redis nor the archive has any frames
- **THEN** the CLI SHALL print "No result frames are available for job {id} in Redis or the database archive." and exit with code 1

#### Scenario: Refresh flag
- **WHEN** `--refresh` is passed without `--result`
- **THEN** the CLI SHALL fail with "--refresh can only be used with --result."
- **AND** `--refresh` together with `--result` is currently a no-op

### Requirement: Result persistence
Unless `--print-only` is set, the CLI SHALL write job results under `--save-dir`, which defaults to `results`. (src: shared/writer.py:21-366; commands/cloud/jobs.py:496-532)

#### Scenario: Cloud layout
- **WHEN** a user runs `sinx cloud jobs result <id> -o out`
- **THEN** JSON files SHALL be written as `out/<agent>/<template_name>/result_NNN.json`
- **AND** packet contents SHALL be written as `result_NNN_<group>_NNN<ext>`, with the extension taken from the MIME type, or `.bin` by default (`.txt` for texts)
- **AND** content referenced by `images`/`texts` packets SHALL be downloaded via `files.fetch`

#### Scenario: Local API layout
- **WHEN** results are saved on a local-api profile
- **THEN** they SHALL be written under `<save_dir>/<agent>/<job_id>/`

#### Scenario: Unsanitized template name
- **WHEN** a template name contains path separators
- **THEN** it is currently used in the output path without sanitization
