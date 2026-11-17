"""Automatic, best-effort telemetry delivery using durable SQLite acknowledgements.

Events are not removed from the pending queue on network failures. Only UUIDs
acknowledged by the server are marked sent. HTTP operations are bounded and
never propagate exceptions into an ordinary CLI command.
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from typing import Any

from sinapsis_cli.telemetry.core import _connect, collection_enabled

DEFAULT_ENDPOINT = 'https://api.sinapsis.tech/api/v1/telemetry/events'
BATCH_SIZE = 40
MAX_BODY_BYTES = 65536
CONNECT_TIMEOUT_SECONDS = 1.5
MAX_PENDING_EVENTS = 10000


def _ensure_schema(conn: sqlite3.Connection) -> None:
    """Add publisher columns without losing events from the prior local patch."""
    columns = {item[1] for item in conn.execute('PRAGMA table_info(events)')}
    if 'lease_until' not in columns:
        conn.execute('ALTER TABLE events ADD COLUMN lease_until REAL DEFAULT 0')
    if 'attempts' not in columns:
        conn.execute('ALTER TABLE events ADD COLUMN attempts INTEGER NOT NULL DEFAULT 0')
    conn.execute('CREATE INDEX IF NOT EXISTS events_pending ON events(sent_at,lease_until)')


def queue_status() -> dict[str, Any]:
    """Report real local delivery state, without creating a database."""
    try:
        conn = _connect()
        if conn is None:
            return {'pending': 0, 'sent': 0, 'last_sent': None}
        with conn:
            _ensure_schema(conn)
            pending = conn.execute('SELECT count(*) FROM events WHERE sent_at IS NULL').fetchone()[0]
            sent = conn.execute('SELECT count(*) FROM events WHERE sent_at IS NOT NULL').fetchone()[0]
            last = conn.execute('SELECT sent_at,payload FROM events WHERE sent_at IS NOT NULL '
                                'ORDER BY sent_at DESC,rowid DESC LIMIT 1').fetchone()
        conn.close()
        return {'pending': int(pending), 'sent': int(sent),
                'last_sent': {'acknowledged_at': last[0], 'payload': json.loads(last[1])} if last else None}
    except (sqlite3.Error, OSError, ValueError):
        return {'pending': 0, 'sent': 0, 'last_sent': None, 'error': 'Could not read telemetry journal'}


def _claim() -> list[dict[str, Any]]:
    """Atomically lease pending events so concurrent CLI processes cannot collide."""
    conn = _connect()
    if conn is None:
        return []
    try:
        conn.execute('BEGIN IMMEDIATE')
        _ensure_schema(conn)
        rows = conn.execute(
            'SELECT event_id,payload FROM events WHERE sent_at IS NULL AND '
            'COALESCE(lease_until,0) <= ? ORDER BY timestamp, rowid LIMIT ?',
            (time.time(), BATCH_SIZE),
        ).fetchall()
        for event_id, _ in rows:
            conn.execute('UPDATE events SET lease_until=?, attempts=attempts+1 WHERE event_id=?',
                         (time.time()+90, event_id))
        conn.commit()
        return [json.loads(row[1]) for row in rows]
    except (OSError, sqlite3.Error, ValueError):
        conn.rollback()
        return []
    finally:
        conn.close()


def _release(ids: set[str], *, acknowledged: set[str]) -> None:
    """Mark only server-acknowledged IDs as sent; release all other leases."""
    try:
        conn = _connect()
        if conn is None:
            return
        with conn:
            for identifier in ids:
                if identifier in acknowledged:
                    conn.execute('UPDATE events SET sent_at=COALESCE(sent_at,?), lease_until=0 WHERE event_id=?',
                                 (datetime.now(UTC).isoformat(timespec='seconds'), identifier))
                else:
                    conn.execute('UPDATE events SET lease_until=0 WHERE event_id=? AND sent_at IS NULL',
                                 (identifier,))
        conn.close()
    except (sqlite3.Error, OSError):
        pass


def _endpoint() -> str | None:
    value = os.getenv('SINAPSIS_TELEMETRY_ENDPOINT', DEFAULT_ENDPOINT)
    parsed = urllib.parse.urlsplit(value)
    if parsed.scheme != 'https' or parsed.username or parsed.password or not parsed.netloc or parsed.query or parsed.fragment:
        return None
    return value


def publish_pending() -> int:
    """Automatically transmit one bounded batch, returning acknowledged count.

    Safe to invoke at every CLI exit. Unreachable telemetry must not affect
    command exit status. One event ID is reused across every retry.
    """
    if not collection_enabled():
        return 0
    endpoint = _endpoint()
    if endpoint is None:
        return 0
    events = _claim()
    if not events:
        return 0
    identifiers = {event['event_id'] for event in events}
    accepted: set[str] = set()
    try:
        # Inventory events can be larger than command events. Never allow one
        # oversized batch to indefinitely prevent every queued event sending.
        while events:
            body = json.dumps({'schema_version': 1, 'events': events}, separators=(',', ':')).encode()
            if len(body) <= MAX_BODY_BYTES:
                break
            events.pop()
        if not events:
            return 0
        request = urllib.request.Request(endpoint, data=body, method='POST',
                                         headers={'Content-Type': 'application/json',
                                                  'User-Agent': 'sinapsis-cli-telemetry/1'})
        with urllib.request.urlopen(request, timeout=CONNECT_TIMEOUT_SECONDS) as response:
            if response.status != 200:
                return 0
            result = json.loads(response.read(16 * 1024))
        ack = result.get('acknowledged') if isinstance(result, dict) else None
        if not isinstance(ack, list) or not all(isinstance(x, str) for x in ack):
            return 0
        accepted = set(ack) & identifiers
        return len(accepted)
    except (OSError, TimeoutError, ValueError, TypeError, urllib.error.URLError):
        return 0
    finally:
        _release(identifiers, acknowledged=accepted)
