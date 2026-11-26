# Usage Telemetry

## Purpose
The CLI and the Local API can collect anonymous usage events and send them to Sinapsis Cloud. Collection is opt-in. Events are queued locally in SQLite and published in batches by an hourly OS-level scheduler.

Citation prefixes:
- `cli:` = `packages/python/cli/sinapsis-cli/src/sinapsis_cli/`
- `api:` = `packages/python/api/sinapsis-api/src/sinapsis_api/`

## Requirements

### Requirement: Opt-in consent
Telemetry SHALL be disabled by default. When `SINAPSIS_TELEMETRY` is set, it SHALL override stored consent, and only the value `"1"` SHALL enable telemetry. (src: cli:telemetry/core.py:65-122)

#### Scenario: Env var disables
- **GIVEN** consent was previously enabled
- **AND** `SINAPSIS_TELEMETRY=0`
- **WHEN** a command runs
- **THEN** no telemetry event SHALL be recorded

#### Scenario: Consent storage
- **WHEN** consent is stored
- **THEN** it SHALL be written to `telemetry.json` with file mode 0600
- **AND** the file SHALL live in `SINAPSIS_TELEMETRY_CONFIG_DIR`, or `user_config_path("sinapsis")` if that variable is unset

### Requirement: Enabling installs a scheduler
`sinx config telemetry enable` SHALL install an hourly OS scheduler that publishes events, and SHALL leave consent false if the installation fails. (src: cli:telemetry/scheduler.py:23-216; cli:commands/common/telemetry.py:54-71)

#### Scenario: Scheduler per OS
- **WHEN** enable runs on Linux
- **THEN** a systemd `--user` timer named `sinapsis-telemetry` SHALL be installed, with cron as the fallback
- **WHEN** enable runs on macOS
- **THEN** a launchd job named `tech.sinapsis.telemetry` with StartInterval 3600 SHALL be installed
- **WHEN** enable runs on Windows
- **THEN** a schtasks task named `SinapsisTelemetry` SHALL be installed

#### Scenario: Scheduler failure
- **WHEN** the scheduler cannot be installed
- **THEN** consent SHALL remain false
- **AND** the CLI SHALL print "Unable to enable automatic telemetry: …" and exit with code 1

### Requirement: Event retention
The CLI SHALL keep telemetry events in `telemetry.sqlite3` under the telemetry state directory, within bounded limits. (src: cli:telemetry/core.py:21-25,65-82)

#### Scenario: Retention limits
- **WHEN** events accumulate
- **THEN** at most 10,000 pending events SHALL be kept
- **AND** at most 200 sent events SHALL be retained
- **AND** events older than 30 days SHALL be purged
- **AND** an inventory snapshot SHALL be taken at most once every 24 h

### Requirement: Event transport
Events SHALL be published by POST to `SINAPSIS_TELEMETRY_ENDPOINT`, which defaults to `https://api.sinapsis.tech/api/v1/telemetry/events`. The endpoint SHALL be HTTPS and SHALL NOT contain credentials, a query string or a fragment. (src: cli:telemetry/transport.py:21-150)

#### Scenario: Insecure endpoint rejected
- **WHEN** `SINAPSIS_TELEMETRY_ENDPOINT=http://example.com/events`
- **THEN** publishing SHALL refuse to send

#### Scenario: Batch limits
- **WHEN** events are published
- **THEN** each batch SHALL contain at most 40 events and its body SHALL be at most 64 KiB
- **AND** each request SHALL time out after 1.5 s, and each batch lease SHALL last 90 s
- **AND** a scheduler run SHALL send at most 25 batches

### Requirement: Telemetry inspection commands
`sinx config telemetry` SHALL provide `status`, `enable`, `disable [--clear]`, `info`, `preview`, `inventory`, `history [--limit 10]`, `clear [--yes]`, `last-sent` and `send`. (src: cli:commands/common/telemetry.py)

#### Scenario: Preview before sending
- **WHEN** a user runs `sinx config telemetry preview`
- **THEN** the pending payload SHALL be printed without being sent

#### Scenario: History limit bounds
- **WHEN** `history --limit 500` is run
- **THEN** the CLI SHALL reject the value, because the allowed range is 1..200

### Requirement: Local API telemetry
The Local API SHALL publish telemetry only when `SINAPSIS_TELEMETRY="1"`. It SHALL publish hourly from a lifespan task and SHALL take an inventory at most once every 24 h. (src: api:telemetry.py:29-35; api:api/main.py:16-34)

#### Scenario: Default container
- **WHEN** the Local API starts with no telemetry environment variables set
- **THEN** no telemetry SHALL be published
- **AND** the state directory SHALL default to `/tmp/sinapsis/telemetry`
