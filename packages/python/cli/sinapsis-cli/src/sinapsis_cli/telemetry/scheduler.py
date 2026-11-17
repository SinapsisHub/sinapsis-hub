"""User-level hourly telemetry delivery using native OS schedulers.

No constantly running daemon and no network I/O in the foreground CLI.
The scheduled process reads the consent file before *every* delivery.
On Linux the preferred backend is systemd --user; cron is a fallback.
macOS uses launchd and Windows uses Task Scheduler (schtasks.exe).
"""
from __future__ import annotations

import json
import os
import plistlib
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from sinapsis_cli.telemetry.core import collection_enabled, config_dir, override_state, record_inventory_if_due
from sinapsis_cli.telemetry.transport import publish_pending

INTERVAL_SECONDS = 3600
SERVICE_NAME = 'sinapsis-telemetry'
LAUNCHD_LABEL = 'tech.sinapsis.telemetry'
TASK_NAME = 'SinapsisTelemetry'


def _state_file() -> Path:
    return config_dir() / 'telemetry-scheduler.json'


def _run(args: list[str], *, stdin: str | None = None) -> subprocess.CompletedProcess[str]:
    """Run a platform scheduler command without a shell or interactive prompt."""
    return subprocess.run(args, input=stdin, capture_output=True, text=True, timeout=8, check=False)


def _scheduler_cmd() -> list[str]:
    return [str(Path(sys.executable).resolve()), '-m', 'sinapsis_cli.telemetry.scheduler', 'run-once']


def _run_script() -> Path:
    """Create a locked-down shell wrapper for systemd or cron."""
    path = config_dir() / 'telemetry-publish.sh'
    cmd = ' '.join(shlex.quote(part) for part in _scheduler_cmd())
    path.write_text('#!/bin/sh\nexec ' + cmd + '\n', encoding='utf-8')
    if os.name == 'posix':
        path.chmod(0o700)
    return path


def _systemd_available() -> bool:
    if not shutil.which('systemctl') or not os.environ.get('XDG_RUNTIME_DIR'):
        return False
    try:
        return _run(['systemctl', '--user', 'show-environment']).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def _install_systemd() -> dict[str, str]:
    location = Path.home() / '.config' / 'systemd' / 'user'
    location.mkdir(parents=True, exist_ok=True)
    script = _run_script()
    service = location / f'{SERVICE_NAME}.service'
    timer = location / f'{SERVICE_NAME}.timer'
    service.write_text('[Unit]\nDescription=Opt-in Sinapsis telemetry publisher\n'
                       '[Service]\nType=oneshot\nExecStart=' + str(script) + '\n', encoding='utf-8')
    timer.write_text('[Unit]\nDescription=Publish opt-in Sinapsis telemetry hourly\n'
                     '[Timer]\nOnBootSec=1h\nOnUnitActiveSec=1h\nPersistent=true\n'
                     f'Unit={SERVICE_NAME}.service\n'
                     '[Install]\nWantedBy=timers.target\n', encoding='utf-8')
    for argv in (['systemctl', '--user', 'daemon-reload'],
                 ['systemctl', '--user', 'enable', '--now', f'{SERVICE_NAME}.timer']):
        result = _run(argv)
        if result.returncode:
            raise RuntimeError('systemd user timer installation failed: ' + result.stderr.strip()[:160])
    return {'provider': 'systemd', 'resource': str(timer)}


def _cron_lines() -> list[str]:
    result = _run(['crontab', '-l'])
    if result.returncode and 'no crontab' not in result.stderr.lower():
        raise RuntimeError('Cannot read user crontab: ' + result.stderr.strip()[:160])
    return result.stdout.splitlines() if result.returncode == 0 else []


def _install_cron() -> dict[str, str]:
    if not shutil.which('crontab'):
        raise RuntimeError('Neither systemd user timers nor crontab are available')
    script = _run_script()
    marker = '# sinapsis-telemetry managed: do not edit this line'
    lines = [line for line in _cron_lines() if marker not in line]
    lines.append('0 * * * * ' + shlex.quote(str(script)) + ' ' + marker)
    result = _run(['crontab', '-'], stdin='\n'.join(lines) + '\n')
    if result.returncode:
        raise RuntimeError('Cron installation failed: ' + result.stderr.strip()[:160])
    return {'provider': 'cron', 'resource': marker}


def _install_launchd() -> dict[str, str]:
    path = Path.home() / 'Library' / 'LaunchAgents' / f'{LAUNCHD_LABEL}.plist'
    path.parent.mkdir(parents=True, exist_ok=True)
    data: dict[str, Any] = {
        'Label': LAUNCHD_LABEL,
        'ProgramArguments': _scheduler_cmd(),
        'StartInterval': INTERVAL_SECONDS,
        'RunAtLoad': False,
        'ProcessType': 'Background',
    }
    path.write_bytes(plistlib.dumps(data))
    path.chmod(0o600)
    domain = f'gui/{os.getuid()}'
    _run(['launchctl', 'bootout', f'{domain}/{LAUNCHD_LABEL}'])
    result = _run(['launchctl', 'bootstrap', domain, str(path)])
    if result.returncode:
        raise RuntimeError('launchd installation failed: ' + result.stderr.strip()[:160])
    return {'provider': 'launchd', 'resource': str(path)}


def _install_windows() -> dict[str, str]:
    # schtasks accepts a single /TR command line; use Windows quoting rules.
    command_line = subprocess.list2cmdline(_scheduler_cmd())
    result = _run(['schtasks', '/Create', '/F', '/SC', 'HOURLY', '/MO', '1',
                   '/TN', TASK_NAME, '/TR', command_line])
    if result.returncode:
        raise RuntimeError('Task Scheduler registration failed: ' + result.stderr.strip()[:160])
    return {'provider': 'windows-task', 'resource': TASK_NAME}


def install_scheduler() -> None:
    """Install the hourly user-level sender; fail rather than pretending it works."""
    if override_state() == '0':
        raise RuntimeError('SINAPSIS_TELEMETRY=0 explicitly disables telemetry in this shell')
    config_dir().mkdir(parents=True, exist_ok=True, mode=0o700)
    if os.name == 'nt':
        state = _install_windows()
    elif sys.platform == 'darwin':
        state = _install_launchd()
    elif sys.platform.startswith('linux'):
        state = _install_systemd() if _systemd_available() else _install_cron()
    else:
        raise RuntimeError(f'Unsupported scheduler operating system: {sys.platform}')
    path = _state_file()
    tmp = path.with_name(path.name + '.tmp')
    try:
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(state, stream)
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def remove_scheduler() -> None:
    """Remove a previously registered scheduler without changing local event history."""
    path = _state_file()
    if not path.exists():
        return
    state = json.loads(path.read_text(encoding='utf-8'))
    provider = state.get('provider')
    if provider == 'systemd':
        result = _run(['systemctl', '--user', 'disable', '--now', f'{SERVICE_NAME}.timer'])
        if result.returncode:
            raise RuntimeError('Could not disable systemd timer: ' + result.stderr.strip()[:160])
        folder = Path.home() / '.config' / 'systemd' / 'user'
        (folder / f'{SERVICE_NAME}.timer').unlink(missing_ok=True)
        (folder / f'{SERVICE_NAME}.service').unlink(missing_ok=True)
        _run(['systemctl', '--user', 'daemon-reload'])
    elif provider == 'cron':
        lines = [line for line in _cron_lines() if state.get('resource', '') not in line]
        result = _run(['crontab', '-'], stdin='\n'.join(lines) + '\n')
        if result.returncode:
            raise RuntimeError('Could not remove cron entry: ' + result.stderr.strip()[:160])
    elif provider == 'launchd':
        _run(['launchctl', 'bootout', f'gui/{os.getuid()}/{LAUNCHD_LABEL}'])
        Path(state['resource']).unlink(missing_ok=True)
    elif provider == 'windows-task':
        result = _run(['schtasks', '/Delete', '/F', '/TN', TASK_NAME])
        if result.returncode:
            raise RuntimeError('Could not remove scheduled task: ' + result.stderr.strip()[:160])
    else:
        raise RuntimeError('Unrecognized scheduler provider; refusing blind removal')
    path.unlink(missing_ok=True)


def scheduler_status() -> dict[str, str]:
    """Check the operating system, not just a local consent Boolean."""
    try:
        state = json.loads(_state_file().read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {'status': 'not installed', 'provider': 'none'}
    provider = state.get('provider', 'unknown')
    try:
        if provider == 'systemd':
            active = _run(['systemctl', '--user', 'is-enabled', f'{SERVICE_NAME}.timer']).returncode == 0
        elif provider == 'cron':
            active = any(state.get('resource') in line for line in _cron_lines())
        elif provider == 'launchd':
            active = _run(['launchctl', 'print', f'gui/{os.getuid()}/{LAUNCHD_LABEL}']).returncode == 0
        elif provider == 'windows-task':
            active = _run(['schtasks', '/Query', '/TN', TASK_NAME]).returncode == 0
        else:
            active = False
    except (OSError, subprocess.TimeoutExpired, RuntimeError):
        active = False
    return {'status': 'active' if active else 'missing/disabled', 'provider': str(provider)}


def run_once() -> int:
    """Refresh due inventory and publish stored batches without an interactive CLI."""
    if not collection_enabled():
        return 0
    record_inventory_if_due()
    total = 0
    for _ in range(25):  # Bounded scheduled execution, maximum 1,000 events.
        sent = publish_pending()
        total += sent
        if sent == 0:
            break
    return total


def main() -> int:
    """Entry point called only by OS schedulers."""
    if sys.argv[1:] != ['run-once']:
        print('Usage: python -m sinapsis_cli.telemetry.scheduler run-once', file=sys.stderr)
        return 2
    run_once()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
