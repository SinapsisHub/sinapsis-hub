"""Opt-in, automatically delivered, container-local Sinapsis package inventory.

This module never inspects other distributions or execution inputs. Its SQLite
queue survives container restarts when /var/lib/sinapsis/telemetry is a volume.
Duplicate retries keep the original event UUID; only acknowledged events are
marked sent. No permanent installation or host identifier is created.
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from importlib import metadata
from pathlib import Path
from uuid import uuid4

MAX_PACKAGES = 100
INTERVAL_SECONDS = 86400
DEFAULT_ENDPOINT = 'https://api.sinapsis.tech/api/v1/telemetry/events'


def enabled() -> bool:
    """Require explicit container consent (independent of the host CLI)."""
    return os.environ.get('SINAPSIS_TELEMETRY', '0').strip() == '1'


def state_dir() -> Path:
    return Path(os.environ.get('SINAPSIS_TELEMETRY_STATE_DIR', '/tmp/sinapsis/telemetry'))


def _connect() -> sqlite3.Connection:
    folder = state_dir()
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = folder / 'container_telemetry.sqlite3'
    conn = sqlite3.connect(path, timeout=2)
    if os.name == 'posix':
        path.chmod(0o600)
    conn.execute('CREATE TABLE IF NOT EXISTS events ('
                 'event_id TEXT PRIMARY KEY, timestamp TEXT NOT NULL, payload TEXT NOT NULL, '
                 'sent_at TEXT, lease_until REAL DEFAULT 0)')
    conn.commit()
    return conn


def inventory() -> dict[str, object]:
    """Inspect only Sinapsis distribution metadata inside this container."""
    distributions: dict[str, str] = {}
    for dist in metadata.distributions():
        name = re.sub(r'[-_.]+', '-', dist.metadata.get('Name', '')).casefold()
        if name == 'sinapsis' or name.startswith('sinapsis-'):
            distributions[name[:120]] = str(dist.version)[:64]
    names = sorted(distributions)
    return {
        'schema_version': 1, 'event_id': str(uuid4()),
        'timestamp': datetime.now(UTC).isoformat(timespec='seconds'),
        'event_type': 'environment.inventory', 'source': 'local-api-container',
        'environment': 'container', 'python': f'{sys.version_info.major}.{sys.version_info.minor}',
        'distributions': [{'name': name, 'version': distributions[name]} for name in names[:MAX_PACKAGES]],
        'distribution_count': len(names), 'truncated': len(names) > MAX_PACKAGES,
    }


def collect_inventory() -> bool:
    """Record at most one inventory per 24h, without blocking local execution."""
    if not enabled():
        return False
    try:
        conn = _connect()
        try:
            row = conn.execute('SELECT timestamp FROM events ORDER BY timestamp DESC LIMIT 1').fetchone()
            if row and (datetime.now(UTC)-datetime.fromisoformat(row[0])).total_seconds() < INTERVAL_SECONDS:
                return False
            event = inventory()
            with conn:
                conn.execute('INSERT INTO events(event_id,timestamp,payload) VALUES(?,?,?)',
                             (event['event_id'], event['timestamp'], json.dumps(event, sort_keys=True)))
        finally:
            conn.close()
        return True
    except (OSError, ValueError, sqlite3.Error):
        return False


def publish_pending() -> int:
    """Automatically send one queue batch, acknowledging only persisted IDs."""
    if not enabled():
        return 0
    endpoint = os.environ.get('SINAPSIS_TELEMETRY_ENDPOINT', DEFAULT_ENDPOINT)
    parsed = urllib.parse.urlsplit(endpoint)
    if parsed.scheme != 'https' or not parsed.netloc or parsed.username or parsed.password:
        return 0
    conn: sqlite3.Connection | None = None
    ids: list[str] = []
    acknowledged: set[str] = set()
    try:
        conn = _connect()
        conn.execute('BEGIN IMMEDIATE')
        rows = conn.execute('SELECT event_id,payload FROM events WHERE sent_at IS NULL '
                            'AND COALESCE(lease_until,0) <= ? ORDER BY timestamp LIMIT 40',
                            (time.time(),)).fetchall()
        for event_id, _ in rows:
            conn.execute('UPDATE events SET lease_until=? WHERE event_id=?', (time.time()+90, event_id))
        conn.commit()
        if not rows:
            return 0
        ids = [row[0] for row in rows]
        events = [json.loads(row[1]) for row in rows]
        while events:
            body = json.dumps({'schema_version': 1, 'events': events}, separators=(',', ':')).encode()
            if len(body) <= 65536:
                break
            events.pop()
        if not events:
            return 0
        request = urllib.request.Request(endpoint, method='POST', data=body,
                                         headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(request, timeout=1.5) as response:
            if response.status != 200:
                return 0
            result = json.loads(response.read(16384))
        ack = result.get('acknowledged') if isinstance(result, dict) else None
        if not isinstance(ack, list) or not all(isinstance(a, str) for a in ack):
            return 0
        acknowledged = set(ids).intersection(ack)
        return len(acknowledged)
    except (OSError, urllib.error.URLError, ValueError, TypeError, sqlite3.Error):
        return 0
    finally:
        if conn is not None:
            try:
                with conn:
                    for event_id in ids:
                        if event_id in acknowledged:
                            conn.execute('UPDATE events SET sent_at=?,lease_until=0 WHERE event_id=?',
                                         (datetime.now(UTC).isoformat(), event_id))
                        else:
                            conn.execute('UPDATE events SET lease_until=0 WHERE event_id=?', (event_id,))
            except sqlite3.Error:
                pass
            conn.close()


def info() -> dict[str, object]:
    """Return exact last sent payload and queue counts for local inspection."""
    if not state_dir().joinpath('container_telemetry.sqlite3').exists():
        return {'enabled': enabled(), 'pending': 0, 'sent': 0, 'last_sent': None}
    try:
        conn = _connect()
        pending = conn.execute('SELECT count(*) FROM events WHERE sent_at IS NULL').fetchone()[0]
        sent = conn.execute('SELECT count(*) FROM events WHERE sent_at IS NOT NULL').fetchone()[0]
        last = conn.execute('SELECT sent_at,payload FROM events WHERE sent_at IS NOT NULL '
                            'ORDER BY sent_at DESC LIMIT 1').fetchone()
        conn.close()
        return {'enabled': enabled(), 'pending': pending, 'sent': sent,
                'last_sent': {'acknowledged_at': last[0], 'payload': json.loads(last[1])} if last else None}
    except (OSError, ValueError, sqlite3.Error):
        return {'enabled': enabled(), 'error': 'Telemetry journal unavailable'}


def main() -> None:
    """Provide transparent local control: info, preview, send or clear."""
    action = sys.argv[1] if len(sys.argv) > 1 else 'info'
    if action == 'info':
        print(json.dumps(info(), indent=2))
        print('Collected: Sinapsis package names/versions, Python version, time, event UUID.')
        print('Never collected: environment variables, paths, execution data or arguments.')
    elif action == 'preview':
        print(json.dumps(inventory(), indent=2))
    elif action == 'send':
        print(f'Acknowledged {publish_pending()} events')
    elif action == 'clear':
        state_dir().joinpath('container_telemetry.sqlite3').unlink(missing_ok=True)
        print('Cleared local container telemetry')
    else:
        raise SystemExit('Usage: python -m sinapsis_api.telemetry [info|preview|send|clear]')


if __name__ == '__main__':
    main()
