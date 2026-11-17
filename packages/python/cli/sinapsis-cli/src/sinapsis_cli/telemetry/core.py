"""Consent, safe telemetry events, and bounded local history for Sinapsis CLI.

This module intentionally has no HTTP client or telemetry ingestion URL. Collection
is disabled by default. Never pass command arguments or job payloads into events.
"""

import json
import os
import re
import sqlite3
import sys
import time
from datetime import UTC, datetime
from importlib import metadata
from pathlib import Path
from typing import Any
from uuid import uuid4

from platformdirs import user_config_path, user_state_path

SCHEMA_VERSION = 1
MAX_EVENTS = 200
MAX_PENDING = 10_000
RETENTION_DAYS = 30
INVENTORY_INTERVAL_SECONDS = 24 * 60 * 60

# Only these literal, fixed command names may enter a command telemetry payload.
# Never use unrecognized positional arguments, even if they look harmless.
_ALLOWED_COMMANDS: dict[str, frozenset[str]] = {
    "jobs": frozenset({"run", "status", "result", "stream", "cancel", "history", "clear", "list", "refresh"}),
    "templates": frozenset({"list", "show", "inspect", "search", "run", "info"}),
    "agents": frozenset({"list", "show", "run", "create", "register", "delete", "versions"}),
    "files": frozenset({"list", "upload", "download", "delete", "search"}),
    "api-keys": frozenset({"list", "create", "revoke", "permissions"}),
    "webhooks": frozenset({"list", "create", "delete", "update"}),
    "schedules": frozenset({"list", "create", "show", "delete", "pause", "resume", "history"}),
    "profiles": frozenset({"list", "create", "show", "delete", "default"}),
    "secrets": frozenset({"list", "create", "delete", "set"}),
}

_FIELD_DESCRIPTIONS: dict[str, str] = {
    "schema_version": "Event schema version (integer).",
    "event_id": "Random per-event UUID; not a persistent user/device identifier.",
    "timestamp": "UTC time when the event was collected.",
    "event_type": "One of cli.command or environment.inventory.",
    "source": "cli only (or a separate local-api container journal).",
    "backend": "Execution backend category, never API URL/profile name.",
    "command": "Whitelisted command category, not flags or argument values.",
    "outcome": "success or error; no error messages or stack traces.",
    "duration_ms": "Rounded CLI command duration, capped at 24 hours.",
    "python": "Python major.minor version only.",
    "cli_version": "Installed Sinapsis CLI distribution version if available.",
    "environment": "cli-runtime or local-venv; never the environment path.",
    "distributions": "Installed sinapsis* distribution names and versions only.",
    "distribution_count": "Number of matching installed distributions before truncation.",
    "truncated": "Whether the inventory was truncated to the first 100 distributions.",
}


def data_fields() -> dict[str, str]:
    """Return descriptions of every field that may be collected."""
    return dict(_FIELD_DESCRIPTIONS)


def config_dir() -> Path:
    """Return the user-level directory for telemetry consent."""
    override = os.environ.get("SINAPSIS_TELEMETRY_CONFIG_DIR")
    return Path(override).expanduser() if override else user_config_path("sinapsis")


def state_dir() -> Path:
    """Return the user-level directory holding private telemetry event history."""
    override = os.environ.get("SINAPSIS_TELEMETRY_STATE_DIR")
    return Path(override).expanduser() if override else user_state_path("sinapsis")


def _consent_path() -> Path:
    return config_dir() / "telemetry.json"


def _db_path() -> Path:
    return state_dir() / "telemetry.sqlite3"


def stored_consent() -> bool:
    """Read opt-in state; missing, invalid, or inaccessible files mean disabled."""
    try:
        content = json.loads(_consent_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return isinstance(content, dict) and content.get("enabled") is True


def set_consent(enabled: bool) -> None:
    """Atomically persist an opt-in/out choice to user-only configuration."""
    folder = config_dir()
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    target = _consent_path()
    tmp = folder / f".telemetry-{uuid4().hex}.tmp"
    try:
        fd = os.open(tmp, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump({"enabled": enabled, "schema_version": SCHEMA_VERSION}, stream)
            stream.write("\n")
        os.replace(tmp, target)
        if os.name == "posix":
            target.chmod(0o600)
    finally:
        tmp.unlink(missing_ok=True)


def override_state() -> str | None:
    """Return the operator's environment override, if explicitly present."""
    return os.environ.get("SINAPSIS_TELEMETRY")


def collection_enabled() -> bool:
    """Determine effective consent; invalid overrides fail closed."""
    override = override_state()
    if override is not None:
        return override.strip() == "1"
    return stored_consent()


def _connect(*, create: bool = False) -> sqlite3.Connection | None:
    """Connect to the local journal without creating files on read-only commands."""
    path = _db_path()
    if not path.exists() and not create:
        return None
    if create:
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    connection = sqlite3.connect(path, timeout=0.1)
    if create:
        if os.name == "posix":
            path.chmod(0o600)
        connection.execute(
            "CREATE TABLE IF NOT EXISTS events ("
            "event_id TEXT PRIMARY KEY, timestamp TEXT NOT NULL, "
            "event_type TEXT NOT NULL, payload TEXT NOT NULL, sent_at TEXT)"
        )
        connection.execute("CREATE INDEX IF NOT EXISTS events_time ON events(timestamp)")
        connection.commit()
    return connection


def new_event(event_type: str, **fields: Any) -> dict[str, Any]:
    """Construct a typed, closed-schema event without user or device identifiers."""
    if event_type not in {"cli.command", "environment.inventory"}:
        raise ValueError("Unsupported telemetry event")
    extras = set(fields) - set(_FIELD_DESCRIPTIONS)
    if extras:
        raise ValueError("Unknown telemetry fields")
    return {
        "schema_version": SCHEMA_VERSION,
        "event_id": str(uuid4()),
        "timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
        "event_type": event_type,
        "source": "cli",
        **fields,
    }


def append_event(event: dict[str, Any]) -> bool:
    """Store an event only with effective consent; never send it over the network."""
    if not collection_enabled():
        return False
    if event.get("event_type") not in {"cli.command", "environment.inventory"}:
        return False
    if set(event) - set(_FIELD_DESCRIPTIONS):
        return False
    try:
        connection = _connect(create=True)
        assert connection is not None
        with connection:
            pending = connection.execute("SELECT COUNT(*) FROM events WHERE sent_at IS NULL").fetchone()[0]
            if pending >= MAX_PENDING:
                return False  # Bounded disk: report backlog; never delete unsent events.
            connection.execute(
                "INSERT INTO events (event_id, timestamp, event_type, payload) VALUES (?, ?, ?, ?)",
                (event["event_id"], event["timestamp"], event["event_type"], json.dumps(event, sort_keys=True)),
            )
            # Only acknowledged history is subject to retention. Pending events
            # MUST survive retries, outages and CLI restarts without silent loss.
            expiry = datetime.fromtimestamp(time.time() - RETENTION_DAYS * 86400, UTC).isoformat()
            connection.execute("DELETE FROM events WHERE sent_at IS NOT NULL AND timestamp < ?", (expiry,))
            connection.execute(
                "DELETE FROM events WHERE event_id IN ("
                "SELECT event_id FROM events WHERE sent_at IS NOT NULL ORDER BY timestamp DESC, rowid DESC LIMIT -1 OFFSET ?) ",
                (MAX_EVENTS,),
            )
        connection.close()
        return True
    except (OSError, sqlite3.Error, KeyError, TypeError, ValueError):
        # Telemetry must never break an ordinary Sinapsis operation.
        return False


def recent_events(limit: int = 10) -> list[dict[str, Any]]:
    """Read bounded local event history, newest first, without any side effects."""
    try:
        connection = _connect()
        if connection is None:
            return []
        with connection:
            rows = connection.execute(
                "SELECT payload FROM events ORDER BY timestamp DESC, rowid DESC LIMIT ?",
                (max(1, min(limit, MAX_EVENTS)),),
            ).fetchall()
        connection.close()
        return [json.loads(row[0]) for row in rows]
    except (OSError, sqlite3.Error, ValueError):
        return []


def clear_events() -> int:
    """Permanently delete the local telemetry journal; leave consent unchanged."""
    try:
        connection = _connect()
        if connection is None:
            return 0
        with connection:
            count = connection.execute("SELECT COUNT(*) FROM events").fetchone()[0]
            connection.execute("DELETE FROM events")
        connection.close()
        return int(count)
    except (OSError, sqlite3.Error):
        return 0


def _cli_version() -> str:
    try:
        return metadata.version("sinapsis-cli")
    except metadata.PackageNotFoundError:
        return "unknown"


def safe_command(arguments: list[str]) -> str | None:
    """Classify only known fixed commands; NEVER return user-provided values."""
    tokens = [token for token in arguments if not token.startswith("-")]
    if not tokens:
        return None
    if tokens[0] == "config":
        return None  # Consent and information queries are deliberately excluded.
    if tokens[0] == "configure":
        return "configure"
    commands = _ALLOWED_COMMANDS.get(tokens[0])
    if commands is None:
        return "other"
    if len(tokens) < 2 or tokens[1] not in commands:
        return f"{tokens[0]}.other"
    return f"{tokens[0]}.{tokens[1]}"


def record_cli_invocation(arguments: list[str], *, backend: str, outcome: str, duration_ms: int) -> None:
    """Record the command category, not command-line arguments or exception text."""
    if not collection_enabled():
        return
    command = safe_command(arguments)
    if command is None:
        return
    append_event(
        new_event(
            "cli.command",
            backend=backend if backend in {"cloud", "local-api", "local-venv"} else "other",
            command=command,
            outcome="success" if outcome == "success" else "error",
            duration_ms=max(0, min(round(duration_ms / 100) * 100, 86400000)),
            python=f"{sys.version_info.major}.{sys.version_info.minor}",
            cli_version=_cli_version(),
        )
    )


def _distribution_paths(venv: Path | None) -> list[str] | None:
    """Select site-packages directories using filesystem metadata; do not execute Python."""
    if venv is None:
        return None  # importlib.metadata uses the running Python environment.
    if not (venv / "pyvenv.cfg").is_file():
        return []
    candidates = [venv / "Lib" / "site-packages", *sorted((venv / "lib").glob("python*/site-packages"))]
    return [str(path) for path in candidates if path.is_dir()]


def inventory_snapshot(*, venv: Path | None = None) -> dict[str, Any]:
    """Scan only installed Sinapsis distributions in the selected environment.

    The scan uses installed wheel metadata, not imports or subprocesses, and
    never collects installed non-Sinapsis packages or the environment path.
    """
    paths = _distribution_paths(venv)
    distributions: dict[str, str] = {}
    if paths != []:
        installed = metadata.distributions() if paths is None else metadata.distributions(path=paths)
        for distribution in installed:
            name = distribution.metadata.get("Name", "")
            normalized = re.sub(r"[-_.]+", "-", name).lower()
            if normalized == "sinapsis" or normalized.startswith("sinapsis-"):
                distributions[normalized[:120]] = str(distribution.version)[:64]
    names = sorted(distributions)
    return {
        "environment": "local-venv" if venv is not None else "cli-runtime",
        "distributions": [{"name": name, "version": distributions[name]} for name in names[:100]],
        "distribution_count": len(names),
        "truncated": len(names) > 100,
        "python": f"{sys.version_info.major}.{sys.version_info.minor}",
    }


def record_inventory_if_due(*, venv: Path | None = None, force: bool = False) -> bool:
    """Collect a privacy-scoped package inventory at most once per 24h/source."""
    if not collection_enabled():
        return False
    source = "local-venv" if venv is not None else "cli-runtime"
    if not force:
        try:
            connection = _connect()
            if connection is not None:
                row = connection.execute(
                    "SELECT timestamp FROM events WHERE event_type = ? AND "
                    "json_extract(payload, '$.environment') = ? ORDER BY timestamp DESC LIMIT 1",
                    ("environment.inventory", source),
                ).fetchone()
                connection.close()
                if row and (datetime.now(UTC) - datetime.fromisoformat(row[0])).total_seconds() < INVENTORY_INTERVAL_SECONDS:
                    return False
        except (OSError, sqlite3.Error, ValueError):
            pass
    try:
        return append_event(new_event("environment.inventory", **inventory_snapshot(venv=venv)))
    except (OSError, ValueError):
        return False
