# CLI Profiles and Configuration (sinx)

## Purpose
`sinapsis-cli` provides the `sinx` command. A named **profile** selects which execution backend `sinx` uses: `local-venv`, `local-api` or `cloud`. The backend in turn determines which command groups are available. Profiles are stored in a TOML file that the SDK also reads.

Citations are relative to `packages/python/cli/sinapsis-cli/` unless they start with `sdk:`, which means `packages/python/sdk/sinapsis-sdk/`.

## Requirements

### Requirement: Console scripts
The package SHALL install four console scripts: `sinx`, `sinx-cloud`, `sinx-venv` and `sinx-api`. `sinx-cloud` SHALL force the `cloud` profile, `sinx-venv` SHALL force `local`, and `sinx-api` SHALL force `local-api`. (src: pyproject.toml:31-35; src/sinapsis_cli/main.py:140-177)

#### Scenario: Forced cloud profile
- **WHEN** a user runs `sinx-cloud jobs list`
- **THEN** the command SHALL behave exactly like `sinx cloud jobs list`

### Requirement: Execution backends
The CLI SHALL support the backends `local-venv`, `local-api` and `cloud`, and SHALL accept `local` and `local_api` as aliases. (src: src/sinapsis_cli/config.py:22-36)

#### Scenario: Backend aliases
- **WHEN** a profile is created with `--backend local`
- **THEN** its backend SHALL be stored as `local-venv`

### Requirement: Built-in profiles
The CLI SHALL ship the built-in profiles `local`, `cloud` and `local-api`, and the default profile SHALL be `local`. (src: src/sinapsis_cli/config.py:11-14,170-191)

#### Scenario: Built-in profile values
- **WHEN** no config file exists
- **THEN** profile `local` SHALL use backend `local-venv` with venv `.venv`
- **AND** profile `cloud` SHALL use `https://api.sinapsis.tech` with `authenticated=True`
- **AND** profile `local-api` SHALL use `http://localhost:8000`
- **AND** commands run without a profile SHALL use `local`

### Requirement: Profile resolution order
When choosing a profile, the CLI SHALL use the first of these that is set: an explicit positional profile token, then `SINAPSIS_PROFILE`, then the legacy variables, then `default_profile`. (src: src/sinapsis_cli/main.py:67-102; src/sinapsis_cli/config.py:259-285)

#### Scenario: Env var overrides default
- **GIVEN** `default_profile = "local"`
- **AND** `SINAPSIS_PROFILE=cloud`
- **WHEN** a user runs `sinx jobs list`
- **THEN** the `cloud` profile SHALL be used

#### Scenario: Positional token detection
- **WHEN** the first non-flag argument, after skipping `--verbose`/`-v`, matches a configured profile name
- **THEN** that argument SHALL be consumed as the explicit profile

#### Scenario: Legacy variables
- **GIVEN** neither a profile token nor `SINAPSIS_PROFILE` is set
- **WHEN** `SINAPSIS_EXECUTION_MODE` is set, or failing that `SINAPSIS_EXECUTE_MODE`
- **THEN** its value SHALL be matched against profile names first and backend aliases second

### Requirement: Backend-specific command composition
The CLI SHALL expose only the command groups that belong to the active profile's backend, plus `configure`, `profiles` and `config telemetry`, which are always available. (src: src/sinapsis_cli/composition.py:117-210)

#### Scenario: Groups per backend
- **WHEN** the backend is `local-venv`
- **THEN** the groups SHALL be `jobs` and `templates`
- **WHEN** the backend is `local-api`
- **THEN** the only group SHALL be `jobs`
- **WHEN** the backend is `cloud`
- **THEN** the groups SHALL be `jobs`, `agents`, `templates`, `files`, `webhooks`, `api-keys`, `packages` and `secrets`

#### Scenario: Cloud-only command on local profile
- **WHEN** a user runs `sinx local secrets list`
- **THEN** the CLI SHALL report that no such command exists

#### Scenario: Unknown command set
- **GIVEN** a profile whose `command_sets` includes an unknown name `x`
- **WHEN** the CLI composes its commands
- **THEN** it SHALL fail with ``Profile {name!r} references unknown command set 'x'.``

### Requirement: Profile management commands
`sinx profiles` SHALL provide the subcommands `list`, `show NAME`, `create NAME --backend B [--api-url] [--venv] [--command-set ...]`, `default NAME` and `delete NAME [--yes]`. (src: src/sinapsis_cli/commands/common/profiles.py:22-139)

#### Scenario: Create a profile
- **WHEN** a user runs `sinx profiles create staging --backend cloud --api-url https://staging.example`
- **THEN** the profile SHALL be saved
- **AND** the CLI SHALL print "Profile 'staging' saved."

#### Scenario: Change default
- **WHEN** a user runs `sinx profiles default cloud`
- **THEN** the CLI SHALL print "Default profile changed to 'cloud'."

### Requirement: Profile name validation
Profile names SHALL match `^[A-Za-z0-9][A-Za-z0-9._-]*$` and SHALL NOT be one of the reserved CLI command names. (src: src/sinapsis_cli/config.py:19,132-141; src/sinapsis_cli/commands/common/profiles.py:22-40)

#### Scenario: Reserved name
- **WHEN** a user runs `sinx profiles create jobs --backend cloud`
- **THEN** the command SHALL fail with "Profile name 'jobs' is reserved by the CLI."
- **AND** the reserved set SHALL be configure, profiles, jobs, templates, files, webhooks, api-keys, secrets, api and version

#### Scenario: Invalid characters
- **WHEN** a profile name starts with `-`
- **THEN** the command SHALL fail with "Profile names must start with a letter or number and contain only letters, numbers, '.', '_', or '-'."

### Requirement: Default profile protection
The CLI SHALL refuse to delete the profile that is currently the default. (src: src/sinapsis_cli/config.py:354-355)

#### Scenario: Delete default
- **GIVEN** `local` is the default profile
- **WHEN** a user runs `sinx profiles delete local --yes`
- **THEN** the command SHALL fail with "Cannot delete the default profile 'local'. Choose another default profile first."
- **AND** the profile SHALL be kept

### Requirement: Interactive configure
`sinx configure [--profile NAME | --all-profiles]` SHALL prompt for the settings of each selected profile's backend, and SHALL then let the user choose a default profile. (src: src/sinapsis_cli/commands/common/auth.py:26-219)

#### Scenario: Prompts per backend
- **WHEN** a `local-venv` profile is configured
- **THEN** the CLI SHALL prompt "Virtual environment" with default `.venv`
- **WHEN** a `local-api` profile is configured
- **THEN** the CLI SHALL prompt "Local API URL" with default `http://localhost:8000`
- **WHEN** a `cloud` profile is configured
- **THEN** the CLI SHALL prompt "Cloud API URL" with default `https://api.sinapsis.tech`, then "Email", then a hidden "Password"

#### Scenario: Wrong password three times
- **WHEN** the cloud login fails
- **THEN** the CLI SHALL print "Login failed. N attempt(s) remaining."
- **AND** after the third failure it SHALL print "Login failed after 3 attempts." and exit with code 1

#### Scenario: Mutually exclusive flags
- **WHEN** both `--profile` and `--all-profiles` are passed
- **THEN** the CLI SHALL fail with "--profile and --all-profiles are mutually exclusive." and exit with code 2

### Requirement: Config storage
The CLI SHALL store its configuration as TOML at `platformdirs.user_config_dir("sinapsis")/config.toml`, using the keys `default_profile` and `profiles.<name>.{backend, authenticated, api_url, venv, command_sets}`. (src: sdk:src/sinapsis_sdk/cloud_api/_config.py:19-27; src/sinapsis_cli/config.py:218-421)

#### Scenario: Legacy key migrated
- **GIVEN** a config file that contains legacy keys such as `active_profile`, `execute_mode`, `base_url` or `execution_mode`
- **WHEN** the config is loaded
- **THEN** those legacy keys SHALL be read
- **AND** when the config is saved, `active_profile` and `execute_mode` SHALL be removed

### Requirement: Error reporting and exit codes
Unless `--verbose`/`-v` is set, the CLI SHALL report an uncaught exception as `Error: {exception}` in red on stderr and exit with code 1. (src: src/sinapsis_cli/main.py:56,121-147)

#### Scenario: Unexpected failure
- **WHEN** a command raises an unexpected exception and `--verbose` is not set
- **THEN** stderr SHALL contain `Error: <message>`
- **AND** the exit code SHALL be 1

#### Scenario: Verbose and usage errors
- **WHEN** `--verbose` is set and a command fails
- **THEN** the full traceback SHALL be shown
- **WHEN** a `BadParameter` usage error occurs
- **THEN** the exit code SHALL be 2
- **WHEN** the user declines a confirmation
- **THEN** the CLI SHALL print "Aborted!" and exit with code 1

### Requirement: Local job history state
The CLI SHALL keep job history in `$SINAPSIS_STATE_DIR/state.json`, which defaults to `~/.local/state/sinapsis`. For each profile, the file SHALL hold the last job id, the 20 most recent jobs and the last agent selection. (src: src/sinapsis_cli/state.py:10-269)

#### Scenario: Implicit last job
- **GIVEN** a job was submitted on profile `cloud`
- **WHEN** a user runs `sinx cloud jobs status` with no JOB_ID
- **THEN** the CLI SHALL show the status of the last job on that profile

#### Scenario: No previous job
- **GIVEN** a profile with no recorded jobs
- **WHEN** a job command is run without a JOB_ID
- **THEN** the CLI SHALL print "No job ID was provided and profile 'p' has no previous job." and exit with code 1

#### Scenario: Clear all profiles
- **WHEN** a user runs `sinx jobs clear --all-profiles`
- **THEN** the CLI SHALL delete the whole state file
- **AND** this currently also deletes the remembered agent selections
