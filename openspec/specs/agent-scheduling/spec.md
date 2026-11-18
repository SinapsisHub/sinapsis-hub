# Agent Scheduling

## Purpose
Sinapsis Cloud can run saved agent versions on a recurring schedule. Schedules are created with `sinx cloud jobs schedule`, then persisted and dispatched server-side, so no local daemon or cron is involved. The models live in `sinapsis-contracts`. The endpoints are under `/api/v1/management/agent-schedules`. The user guide is `packages/python/cli/sinapsis-cli/SCHEDULING.md`.

Citation prefixes:
- `cli:` = `packages/python/cli/sinapsis-cli/src/sinapsis_cli/commands/cloud/`
- `contracts:` = `packages/python/sdk/sinapsis-contracts/src/sinapsis_contracts/cloud_api/scheduling/`

## Requirements

### Requirement: Single recurrence mode
A schedule SHALL use exactly one recurrence mode: `ONCE`, `DAILY`, `WEEKLY` or `INTERVAL`. (src: cli:schedules.py:84-85; contracts:schemas.py:20-100)

#### Scenario: Zero or multiple modes
- **WHEN** a user passes none of the mode flags, or more than one
- **THEN** the CLI SHALL fail with "Choose exactly one of --once, --daily, --weekly, or --every-hours"

#### Scenario: Mismatched fields
- **WHEN** a recurrence payload's fields do not match its `schedule_type`
- **THEN** validation SHALL fail with "Recurrence fields do not match schedule_type"

### Requirement: One-time schedules
`--once` SHALL take an ISO 8601 timestamp that includes an explicit offset. (src: cli:schedules.py:51-59)

#### Scenario: Once without offset
- **WHEN** a user passes `--once 2026-12-01T09:00:00`
- **THEN** the CLI SHALL fail with "--once requires an explicit offset, e.g. +00:00 or Z"

#### Scenario: Malformed timestamp
- **WHEN** the value is not ISO 8601
- **THEN** the CLI SHALL fail with "Expected ISO 8601, e.g. 2026-12-01T09:00:00+00:00"

### Requirement: Daily and weekly schedules
`--daily` and `--weekly` SHALL take a local time `HH:MM[:SS]` without an offset. `--weekly` SHALL also require at least one `--weekday` from `mon` to `sun`. (src: cli:schedules.py:62-102)

#### Scenario: Offset in local time
- **WHEN** a user passes `--daily 09:00+02:00`
- **THEN** the CLI SHALL fail with "Use --timezone for daily/weekly times, not a time offset"

#### Scenario: Weekly without weekday
- **WHEN** a user passes `--weekly 09:00` with no `--weekday`
- **THEN** the CLI SHALL fail with "--weekly requires at least one --weekday (mon to sun)"

#### Scenario: Weekday normalization
- **WHEN** a user passes `--weekday fri --weekday mon --weekday fri`
- **THEN** the weekdays SHALL be stored de-duplicated and sorted, with Monday as 0
- **AND** using `--weekday` without `--weekly` SHALL fail with "--weekday requires --weekly"

### Requirement: Interval schedules
`--every-hours N` SHALL accept a positive whole number N and store it as N×3600 seconds. The contract bounds the interval to 60–31,536,000 seconds. (src: cli:schedules.py:103-109; contracts:schemas.py:58)

#### Scenario: Non-positive interval
- **WHEN** a user passes `--every-hours 0`
- **THEN** the CLI SHALL fail with "--every-hours must be a positive whole number"

### Requirement: Schedule timezone
`--timezone` SHALL be an IANA name of 1–80 characters, validated with `ZoneInfo`, and SHALL default to `UTC` on create. (src: cli:schedules.py:31,252; contracts:schemas.py:54,63-66)

#### Scenario: Unknown timezone
- **WHEN** a user passes `--timezone Mars/Base`
- **THEN** validation SHALL fail with "Unknown IANA timezone"

### Requirement: Schedule creation and agent selection
`schedule create --name NAME [--agent-id] [--agent-version-id] [--preset-id]` SHALL create a schedule for an agent version resolved from the flags and the profile's remembered selection. `--name` SHALL be 1–160 characters. (src: cli:schedules.py:207-281)

#### Scenario: Schedule the just-registered agent
- **GIVEN** a user just ran `sinx cloud agents register a.yml --version v1`
- **WHEN** they run `sinx cloud jobs schedule create --name nightly --daily 02:00 --timezone Europe/Madrid`
- **THEN** a DAILY schedule for that agent version SHALL be created
- **AND** the CLI SHALL print "Schedule created."

#### Scenario: Agent only
- **WHEN** only `--agent-id` is given
- **THEN** the newest version of that agent SHALL be used, ordered by `created_at` then id

#### Scenario: Version only
- **WHEN** only `--agent-version-id` is given
- **THEN** the remembered agent SHALL be used with that version
- **AND** a version that belongs to a different agent SHALL fail with "Version does not belong to the specified agent"

#### Scenario: Nothing remembered
- **WHEN** neither flag is given and no selection is remembered
- **THEN** the CLI SHALL fail with "No selected agent; provide --agent-id or register one"

### Requirement: Schedule lifecycle commands
The schedule commands SHALL provide `list [--limit 100]`, `show ID`, `update ID`, `pause ID`, `resume ID`, `delete ID [--yes]` and `runs ID [--limit 100]`. A schedule SHALL be `ACTIVE`, `PAUSED` or `COMPLETED`. (src: cli:schedules.py:169-376; contracts:schemas.py:20-34)

#### Scenario: Pause and resume
- **WHEN** a user runs `schedule pause <id>` and then `schedule resume <id>`
- **THEN** the SDK SHALL send `PATCH {status: PAUSED}` and then `PATCH {status: ACTIVE}`

#### Scenario: Soft delete
- **WHEN** a user runs `schedule delete <id>` and confirms
- **THEN** the schedule SHALL be disabled and its history kept
- **AND** the CLI SHALL print "Schedule disabled: <id>"

#### Scenario: Run history
- **WHEN** a user runs `schedule runs <id>`
- **THEN** a "Scheduled runs" table SHALL show Scheduled for, Status, Job ID, Attempts and Error
- **AND** each run status SHALL be one of PENDING, CLAIMED, ENQUEUED or FAILED

### Requirement: Schedule update rules
`schedule update ID` SHALL send a PATCH that contains only the changed `name` and/or a complete new recurrence. (src: cli:schedules.py:307-338)

#### Scenario: Partial recurrence update
- **WHEN** a user runs `schedule update <id> --timezone UTC` without a recurrence mode
- **THEN** the CLI SHALL fail with "Changing timezone or weekdays requires a full recurrence mode"

#### Scenario: Recurrence without timezone
- **WHEN** a new recurrence mode is given without `--timezone`
- **THEN** the CLI SHALL fail with "Specify --timezone when replacing a recurrence"

#### Scenario: Nothing to update
- **WHEN** neither `--name` nor a recurrence mode is given
- **THEN** the CLI SHALL fail with "Provide --name or a new recurrence"
