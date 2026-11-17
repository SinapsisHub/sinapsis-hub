<h1 align="center">
<br>
<a href="https://sinapsis.tech/">
  <img
    src="https://github.com/SinapsisHub/brand-resources/blob/main/public/logo/sinapsis-logo-horizontal-dark-brand.png?raw=true"
    alt="Sinapsis"
    width="300">
</a>
<br>
Saved Agents & Scheduling
<br>
</h1>

<p align="center">Sinapsis Cloud CLI reference for immutable Agent versions and scheduled execution.</p>

[← Back to Sinapsis CLI](README.md)

## Before you start

Install `sinapsis-cli` (Python 3.13+) and configure your Cloud profile:

```bash
sinx-cloud configure
sinx-cloud profiles show cloud
```

Don't have an account yet? Visit **[sinapsis.tech](https://sinapsis.tech/)** to create one.

For a list of commands:

```bash
sinx-cloud agents --help
sinx-cloud jobs schedule --help
sinx-cloud jobs schedule create --help
```

**Immediate execution and scheduled execution are different:**

- `sinx-cloud jobs run agent.yaml` submits a YAML Agent definition immediately. You do **not** need to register it first.
- A schedule references a **saved Agent and one immutable version**. When the schedule runs, it uses that saved definition—not a file from your computer.

## 1. Register a saved Agent

Register a reusable Agent definition without starting a job:

```bash
sinx-cloud agents register report.yaml --version v1
```

`--version` is **required**. You can also specify a display name:

```bash
sinx-cloud agents register report.yaml \
  --version v1 \
  --name "Daily report"
```

The command returns an **Agent ID** and a **Version ID**. They identify different things:

| Identifier | Meaning |
| --- | --- |
| Agent ID | The saved Agent that can have multiple published versions. |
| Version ID | One immutable snapshot of that Agent's definition. |
| Schedule ID | The recurrence configuration that references an Agent version. |
| Job ID | One individual execution, including one dispatched by a schedule. |

The CLI also remembers the registered Agent and version so the next scheduling command does not need the UUIDs repeated.

### Browse Agents and versions

```bash
sinx-cloud agents list
sinx-cloud agents versions AGENT_UUID
sinx-cloud agents version AGENT_UUID VERSION_UUID
```

Use `agents version` to display the stored Agent definition. When `AGENT_UUID` and `VERSION_UUID` are omitted, it uses the remembered Agent/version selection, where available:

```bash
sinx-cloud agents version
```

To list versions of all explicitly registered Agents:

```bash
sinx-cloud agents versions
```

By default, `agents list` and the no-argument `agents versions` view focus on explicitly registered Agents. Add `--all` to include execution-created and earlier records:

```bash
sinx-cloud agents list --all
sinx-cloud agents versions --all
```

## 2. Create a schedule

Exactly **one recurrence mode** must be supplied:

| Mode | Option | Behaviour |
| --- | --- | --- |
| One-time | `--once TIMESTAMP` | Executes once at a specific offset-aware timestamp. |
| Daily | `--daily HH:MM` | Executes every day at the chosen local time. |
| Weekly | `--weekly HH:MM` | Executes on specified weekdays at the chosen local time. |
| Interval | `--every-hours N` | Executes on a fixed elapsed-hours interval. |

Each schedule is associated with a saved Agent version. The commands below use the most recently selected Agent and version; see [Agent/version selection](#3-agentversion-selection) to pass explicit IDs.

### Daily

```bash
sinx-cloud agents register report.yaml --version v1

sinx-cloud jobs schedule create \
  --name morning-report \
  --daily 09:00 \
  --timezone Europe/London
```

Daily and weekly schedules use an **IANA timezone**. `Europe/London` follows local clock time through daylight-saving changes.

### One-time

```bash
sinx-cloud jobs schedule create \
  --name one-off-export \
  --once 2026-12-01T09:00:00+00:00
```

One-time timestamps must include a timezone offset (for example, `+00:00` or `Z`).

### Weekly

```bash
sinx-cloud jobs schedule create \
  --name weekly-sync \
  --weekly 17:00 \
  --weekday mon \
  --weekday fri \
  --timezone Europe/London
```

`--weekly` requires at least one `--weekday`. Valid values: `mon`, `tue`, `wed`, `thu`, `fri`, `sat`, `sun`. Repeat `--weekday` to select more than one day.

### Fixed interval

```bash
sinx-cloud jobs schedule create \
  --name periodic-ingestion \
  --every-hours 6
```

Intervals represent elapsed time, not a fixed local clock hour. `--every-hours` must be a positive whole number.

### Explicit Agent/version IDs

You can pin a new schedule to a particular version:

```bash
sinx-cloud jobs schedule create \
  --name pinned-report \
  --agent-id AGENT_UUID \
  --agent-version-id VERSION_UUID \
  --daily 09:00 \
  --timezone Europe/London
```

An optional saved preset can be supplied with `--preset-id PRESET_UUID` when applicable:

```bash
sinx-cloud jobs schedule create \
  --name report-with-preset \
  --agent-id AGENT_UUID \
  --agent-version-id VERSION_UUID \
  --preset-id PRESET_UUID \
  --daily 09:00 \
  --timezone Europe/London
```

## 3. Agent/version selection

The CLI remembers the last selected saved Agent and version for your current profile. That allows commands such as:

```bash
sinx-cloud agents register report.yaml --version v1
sinx-cloud jobs schedule create --name morning-report --daily 09:00
```

When creating a schedule, the selection rules are:

| Supplied options | Version used |
| --- | --- |
| Neither `--agent-id` nor `--agent-version-id` | The last selected saved Agent and version. |
| `--agent-id` only | The newest version of the specified Agent. |
| `--agent-version-id` only | That version, checked against the previously selected Agent. |
| Both options | The explicitly supplied Agent/version pair, checked for a match. |

If there is no remembered Agent, provide `--agent-id` or register one first. The CLI's remembered selection is a convenience; it does not grant access to Agents you cannot otherwise use.

Viewing a specific version updates the remembered selection:

```bash
sinx-cloud agents version AGENT_UUID VERSION_UUID
```

## 4. Publish a new version

Saved versions are immutable. To change an Agent definition, publish a new version:

```bash
sinx-cloud agents publish AGENT_UUID updated-report.yaml --version v2
```

The CLI remembers `v2` as the selected version for subsequent commands. **Existing schedules do not automatically move to `v2`.** A schedule pinned to `v1` continues to reference that original definition.

To create a new daily schedule for the updated Agent version:

```bash
sinx-cloud jobs schedule create \
  --name report-v2 \
  --daily 10:00 \
  --timezone Europe/London
```

This uses the latest selected version (`v2`, after publishing). To target a different version deliberately, provide its IDs explicitly.

## 5. Manage schedules

```bash
# List schedules
sinx-cloud jobs schedule list
sinx-cloud jobs schedule list --limit 50

# Inspect the recurrence and next execution
sinx-cloud jobs schedule show SCHEDULE_UUID

# Rename without changing the recurrence
sinx-cloud jobs schedule update SCHEDULE_UUID --name updated-name

# Replace the complete recurrence (including timezone)
sinx-cloud jobs schedule update SCHEDULE_UUID \
  --daily 08:30 \
  --timezone Europe/London

# Pause and resume future dispatches
sinx-cloud jobs schedule pause SCHEDULE_UUID
sinx-cloud jobs schedule resume SCHEDULE_UUID

# Disable a schedule (its run history is retained)
sinx-cloud jobs schedule delete SCHEDULE_UUID
sinx-cloud jobs schedule delete SCHEDULE_UUID --yes
```

For a recurrence update, pass a complete replacement mode (`--once`, `--daily`, `--weekly`, or `--every-hours`) and `--timezone`; a timezone or weekday alone cannot update the schedule. To rename a schedule, `--name` can be provided on its own.

`delete` prompts for confirmation by default. `--yes` skips the prompt.

## 6. Inspect scheduled runs

Each scheduled occurrence is tracked separately. The run history includes the scheduled time, dispatch status, job ID, attempts, and any dispatch error:

```bash
sinx-cloud jobs schedule runs SCHEDULE_UUID
sinx-cloud jobs schedule runs SCHEDULE_UUID --limit 50
```

Inspect one dispatched execution using its job ID:

```bash
sinx-cloud jobs status JOB_ID
sinx-cloud jobs result JOB_ID
sinx-cloud jobs stream JOB_ID
```

These job commands accept explicit IDs even when the execution did not originate in your current terminal. A newly created schedule may have no runs until its first occurrence is due.

## 7. Full example

```bash
# 1. Save a reusable Agent at version v1
sinx-cloud agents register report.yaml --version v1

# 2. Schedule that version for 09:00 London time
sinx-cloud jobs schedule create \
  --name daily-report \
  --daily 09:00 \
  --timezone Europe/London

# 3. View the created schedule
sinx-cloud jobs schedule list
sinx-cloud jobs schedule show SCHEDULE_UUID

# 4. Publish a new immutable version
sinx-cloud agents publish AGENT_UUID updated-report.yaml --version v2

# 5. Create another schedule for v2; the original still uses v1
sinx-cloud jobs schedule create \
  --name daily-report-v2 \
  --daily 10:00 \
  --timezone Europe/London

# 6. Check dispatch history after a scheduled occurrence
sinx-cloud jobs schedule runs SCHEDULE_UUID
sinx-cloud jobs status JOB_ID
```

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| No saved Agent is selected | Register an Agent with `--version`, or pass `--agent-id` explicitly. |
| Agent version is missing or invalid | Run `sinx-cloud agents versions AGENT_UUID` and check the version ID. |
| Cannot access an Agent or version | Confirm you are using the intended Cloud account and saved Agent IDs. |
| Schedule has no runs | Check `sinx-cloud jobs schedule show SCHEDULE_UUID`, including its status and next run time. |
| A scheduled job has no result yet | Inspect `sinx-cloud jobs status JOB_ID` to see whether execution has finished. |
| Schedule requests fail | Check `sinx-cloud profiles show cloud` and that the Cloud service is available. |

## Command reference

| Command | Purpose |
| --- | --- |
| `agents register FILE --version LABEL` | Save an Agent and its first version. |
| `agents list [--all]` | List saved Agents. |
| `agents versions [AGENT_ID] [--all]` | List immutable versions. |
| `agents version [AGENT_ID] [VERSION_ID]` | Inspect a saved version and definition. |
| `agents publish AGENT_ID FILE --version LABEL` | Publish an immutable revision. |
| `jobs schedule create` | Create a new schedule. |
| `jobs schedule list` | List schedules. |
| `jobs schedule show SCHEDULE_ID` | Show schedule details. |
| `jobs schedule update SCHEDULE_ID` | Rename or replace recurrence. |
| `jobs schedule pause SCHEDULE_ID` | Pause future occurrences. |
| `jobs schedule resume SCHEDULE_ID` | Resume future occurrences. |
| `jobs schedule delete SCHEDULE_ID` | Disable a schedule. |
| `jobs schedule runs SCHEDULE_ID` | View dispatch history. |
| `jobs status [JOB_ID]` | Inspect an execution. |
| `jobs result [JOB_ID]` | Retrieve execution results. |

[← Back to Sinapsis CLI](README.md) · [Sinapsis documentation](https://docs.sinapsis.tech/) · [Tutorials and examples](https://docs.sinapsis.tech/docs/latest/tutorials)