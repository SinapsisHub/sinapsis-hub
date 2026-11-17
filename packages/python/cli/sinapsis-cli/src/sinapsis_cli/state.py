"""Persistent local state for the Sinapsis CLI."""

import json
import os
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

APP_NAME = "sinapsis"
STATE_DIR = Path(os.environ.get("SINAPSIS_STATE_DIR", Path.home() / ".local" / "state" / APP_NAME))
STATE_FILE = STATE_DIR / "state.json"

MAX_RECENT_JOBS = 20


@dataclass
class JobRecord:
    """Local metadata about a job submitted through the CLI."""

    job_id: str
    source: str | None
    target: str | None
    profile: str | None
    backend: str | None
    submitted_at: str


@dataclass
class CLIState:
    """Persistent state maintained by the CLI."""

    last_job_ids: dict[str, str] | None = None
    jobs: list[JobRecord] | None = None
    legacy_last_job_id: str | None = None
    last_agent_selections: dict[str, dict[str, str]] | None = None

    def __post_init__(self) -> None:
        if self.last_job_ids is None:
            self.last_job_ids = {}
        if self.jobs is None:
            self.jobs = []
        if self.last_agent_selections is None:
            self.last_agent_selections = {}


def load_state() -> CLIState:
    """Load CLI state from disk.

    Missing or invalid state is treated as empty state. The previous single
    ``last_job_id`` field is retained in memory as a migration fallback.
    """
    if not STATE_FILE.exists():
        return CLIState()

    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return CLIState()

    if not isinstance(data, dict):
        return CLIState()

    last_job_ids: dict[str, str] = {}
    raw_last_job_ids = data.get("last_job_ids", {})

    if isinstance(raw_last_job_ids, dict):
        for profile, job_id in raw_last_job_ids.items():
            if isinstance(profile, str) and isinstance(job_id, str):
                last_job_ids[profile] = job_id

    legacy_last_job_id = data.get("last_job_id")
    if not isinstance(legacy_last_job_id, str):
        legacy_last_job_id = None

    jobs: list[JobRecord] = []
    raw_jobs = data.get("jobs", [])

    if isinstance(raw_jobs, list):
        for item in raw_jobs:
            if not isinstance(item, dict):
                continue

            job_id = item.get("job_id")
            submitted_at = item.get("submitted_at")

            if not isinstance(job_id, str) or not isinstance(submitted_at, str):
                continue

            source = item.get("source")
            target = item.get("target")
            profile = item.get("profile")
            backend = item.get("backend")

            jobs.append(
                JobRecord(
                    job_id=job_id,
                    source=source if isinstance(source, str) else None,
                    target=target if isinstance(target, str) else None,
                    profile=profile if isinstance(profile, str) else None,
                    backend=backend if isinstance(backend, str) else None,
                    submitted_at=submitted_at,
                )
            )

    selections: dict[str, dict[str, str]] = {}
    raw_selections = data.get("last_agent_selections", {})
    if isinstance(raw_selections, dict):
        for profile, entry in raw_selections.items():
            if not isinstance(profile, str) or not isinstance(entry, dict):
                continue
            try:
                agent_id = UUID(str(entry["agent_id"]))
                version_id = UUID(str(entry["agent_version_id"]))
            except (ValueError, TypeError, KeyError, AttributeError):
                continue
            selections[profile] = {"agent_id": str(agent_id), "agent_version_id": str(version_id)}

    return CLIState(
        last_job_ids=last_job_ids,
        jobs=jobs,
        legacy_last_job_id=legacy_last_job_id,
        last_agent_selections=selections,
    )


def save_state(state: CLIState) -> None:
    """Persist CLI state to disk."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    data = {
        "last_job_ids": state.last_job_ids or {},
        "last_agent_selections": state.last_agent_selections or {},
        "jobs": [asdict(job) for job in state.jobs or []],
    }

    STATE_FILE.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def record_job(
    job_id: str, *, source: str | Path | None = None, target: str | None, profile: str, backend: str
) -> JobRecord:
    """Record a newly submitted job for a profile."""
    state = load_state()

    record = JobRecord(
        job_id=job_id,
        source=str(source) if source is not None else None,
        target=target,
        profile=profile,
        backend=backend,
        submitted_at=datetime.now(UTC).isoformat(),
    )

    candidates = [record, *(job for job in state.jobs or [] if job.job_id != job_id)]

    # Retention is profile-scoped so activity in one environment does not
    # evict another profile's recent jobs. Legacy unscoped records share their
    # own bucket.
    retained: list[JobRecord] = []
    counts: dict[str | None, int] = {}

    for candidate in candidates:
        bucket = candidate.profile
        count = counts.get(bucket, 0)
        if count >= MAX_RECENT_JOBS:
            continue

        retained.append(candidate)
        counts[bucket] = count + 1

    state.jobs = retained

    assert state.last_job_ids is not None
    state.last_job_ids[profile] = job_id

    save_state(state)
    return record


def get_last_job_id(profile: str | None = None) -> str | None:
    """Return the most recently submitted job ID.

    If ``profile`` is supplied, only that profile's history is considered.
    Legacy state falls back to the previous global last-job value when the
    referenced record was not assigned to a profile.
    """
    state = load_state()

    if profile is None:
        jobs = state.jobs or []
        return jobs[0].job_id if jobs else state.legacy_last_job_id

    assert state.last_job_ids is not None
    job_id = state.last_job_ids.get(profile)
    if job_id is not None:
        return job_id

    return None


def get_job(job_id: str, *, state: CLIState | None = None) -> JobRecord | None:
    """Return a locally recorded job by ID."""
    state = state or load_state()

    for job in state.jobs or []:
        if job.job_id == job_id:
            return job

    return None


def list_jobs(profile: str | None = None) -> list[JobRecord]:
    """Return locally recorded jobs, newest first."""
    jobs = list(load_state().jobs or [])

    if profile is None:
        return jobs

    return [job for job in jobs if job.profile == profile]


def clear_jobs(profile: str) -> None:
    """Remove job history for one profile."""
    state = load_state()
    state.jobs = [job for job in state.jobs or [] if job.profile != profile]

    assert state.last_job_ids is not None
    state.last_job_ids.pop(profile, None)
    save_state(state)


def migrate_legacy_job_state(config) -> None:
    """Assign legacy unscoped API jobs to profiles when ownership is unambiguous.

    Legacy records did not persist a profile or backend. A record is migrated
    only when its target URL matches exactly one configured API-backed profile.
    Ambiguous records are intentionally left untouched rather than guessed.
    """
    state = load_state()
    profiles = getattr(config, "profiles", None) or {}
    changed = False

    for job in state.jobs or []:
        if job.profile is not None or job.target is None:
            continue

        matches = [profile for profile in profiles.values() if getattr(profile, "api_url", None) == job.target]

        if len(matches) != 1:
            continue

        profile = matches[0]
        job.profile = profile.name
        job.backend = profile.backend.value
        changed = True

        if state.legacy_last_job_id == job.job_id:
            assert state.last_job_ids is not None
            state.last_job_ids.setdefault(profile.name, job.job_id)

    if changed:
        save_state(state)


def clear_state() -> None:
    """Remove all locally stored CLI state."""
    if STATE_FILE.exists():
        STATE_FILE.unlink()


def record_agent_selection(profile: str, agent_id: UUID, agent_version_id: UUID) -> None:
    """Remember a verified, immutable agent/version pair per Cloud profile."""
    state = load_state()
    assert state.last_agent_selections is not None
    state.last_agent_selections[profile] = {
        "agent_id": str(agent_id),
        "agent_version_id": str(agent_version_id),
    }
    save_state(state)


def get_agent_selection(profile: str) -> tuple[UUID, UUID] | None:
    """Retrieve the last successfully selected agent and version."""
    selections = load_state().last_agent_selections or {}
    entry = selections.get(profile)
    if entry is None:
        return None
    return UUID(entry["agent_id"]), UUID(entry["agent_version_id"])


@dataclass(frozen=True, slots=True)
class SavedAgentSelection:
    """Legacy read shape for a persisted saved-agent selection."""

    agent_id: str
    agent_version_id: str


def record_saved_agent(scope: str, agent_id: str | UUID, agent_version_id: str | UUID) -> None:
    """Compatibility wrapper: reuse the canonical agent-selection state."""
    record_agent_selection(scope, UUID(str(agent_id)), UUID(str(agent_version_id)))


def get_saved_agent(scope: str) -> SavedAgentSelection | None:
    """Compatibility wrapper: reuse the canonical agent-selection state."""
    pair = get_agent_selection(scope)
    if pair is None:
        return None
    return SavedAgentSelection(agent_id=str(pair[0]), agent_version_id=str(pair[1]))
