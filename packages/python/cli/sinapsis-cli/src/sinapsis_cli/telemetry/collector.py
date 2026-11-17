"""Detached, local-only event collector for short-lived CLI processes.

The foreground CLI never scans installed distributions, writes SQLite, or
performs HTTP telemetry operations. It passes only an allowlisted command
category to this subprocess; raw command arguments are never passed onward.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from sinapsis_cli.telemetry.core import collection_enabled, record_cli_invocation, record_inventory_if_due, safe_command

_ALLOWED_BACKENDS = frozenset({'cloud', 'local-api', 'local-venv', 'other'})


def spawn_collector(
    args: list[str], *, backend: str, outcome: str, duration_ms: int, venv: str | None = None,
) -> bool:
    """Spawn an independent, local writer; never block to await its completion.

    The spawned process performs no network calls and exits after bounded
    local database writes. A process crash before its write is durable may
    lose this event; successfully queued events are retried until acknowledged.
    """
    if not collection_enabled():
        return False
    command = safe_command(args)
    if command is None:
        return False
    argv = [
        sys.executable, '-m', 'sinapsis_cli.telemetry.collector', 'write',
        '--command', command,
        '--backend', backend if backend in _ALLOWED_BACKENDS else 'other',
        '--outcome', 'success' if outcome == 'success' else 'error',
        '--duration-ms', str(max(0, min(duration_ms, 86400000))),
    ]
    if venv:
        argv.extend(('--venv', str(Path(venv).expanduser().resolve())))
    # Do not forward the original raw CLI arguments; all child arguments are
    # validated fixed categories, durations, and optionally a *local-only*
    # selected virtual-environment path. Its path never enters event payloads.
    kwargs: dict[str, object] = {'stdin': subprocess.DEVNULL,
                                 'stdout': subprocess.DEVNULL,
                                 'stderr': subprocess.DEVNULL,
                                 'close_fds': True}
    if os.name == 'nt':
        kwargs['creationflags'] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs['start_new_session'] = True
    try:
        subprocess.Popen(argv, **kwargs)
        return True
    except (OSError, ValueError):
        return False


def main() -> int:
    """Write a sanitized command event and a cached local environment inventory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['write'])
    parser.add_argument('--command', required=True)
    parser.add_argument('--backend', choices=sorted(_ALLOWED_BACKENDS), required=True)
    parser.add_argument('--outcome', choices=['success', 'error'], required=True)
    parser.add_argument('--duration-ms', type=int, required=True)
    parser.add_argument('--venv', type=Path)
    args = parser.parse_args()
    if not collection_enabled():
        return 0
    # Re-validate the category in case a process invokes this directly.
    allowed = safe_command(args.command.split('.', 1))
    if allowed != args.command:
        return 1
    record_cli_invocation(args.command.split('.'), backend=args.backend, outcome=args.outcome,
                          duration_ms=args.duration_ms)
    record_inventory_if_due(venv=args.venv)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
