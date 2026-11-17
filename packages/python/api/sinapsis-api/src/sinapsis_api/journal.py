"""Per-agent bounded event journals with stateless replay/live consumers."""

import asyncio
import time
from collections import deque
from dataclasses import dataclass, field

from sinapsis.logging import sinapsis_logger

from sinapsis_api.protocol import EventRecord


@dataclass(frozen=True, slots=True)
class JournalWindow:
    """Current retained window for one agent stream."""

    stream_id: str
    agent_id: str
    oldest_cursor: int
    latest_cursor: int
    event_count: int
    size_bytes: int


@dataclass(frozen=True, slots=True)
class ReplayResult:
    """A bounded replay result and its retained-window metadata."""

    events: tuple[EventRecord, ...]
    window: JournalWindow
    requested_after: int
    effective_after: int
    truncated: bool
    has_more: bool
    next_cursor: int


@dataclass(slots=True)
class Subscription:
    """Ephemeral live subscriber state; never persisted as consumer state."""

    queue: asyncio.Queue[EventRecord]
    after: int
    job_id: str | None
    closed: bool = False


@dataclass(slots=True)
class _AgentJournal:
    stream_id: str
    agent_id: str
    max_events: int
    max_bytes: int
    retention_ns: int
    events: deque[EventRecord] = field(default_factory=deque)
    next_cursor: int = 1
    size_bytes: int = 0
    stopped_ns: int | None = None
    subscriptions: dict[int, Subscription] = field(default_factory=dict)
    next_subscription_id: int = 1

    def prune(self, now_ns: int) -> None:
        cutoff = now_ns - self.retention_ns
        while self.events and (
            len(self.events) > self.max_events or self.size_bytes > self.max_bytes or self.events[0].created_ns < cutoff
        ):
            removed = self.events.popleft()
            self.size_bytes -= removed.size_bytes

    def window(self) -> JournalWindow:
        oldest = self.events[0].cursor if self.events else self.next_cursor
        return JournalWindow(
            stream_id=self.stream_id,
            agent_id=self.agent_id,
            oldest_cursor=oldest,
            latest_cursor=self.next_cursor - 1,
            event_count=len(self.events),
            size_bytes=self.size_bytes,
        )


class AgentEventJournals:
    """Own independent rolling event streams keyed by logical agent ID."""

    def __init__(
        self,
        *,
        stream_id: str,
        retention_seconds: float,
        max_events: int,
        max_bytes: int,
        max_event_bytes: int,
        stopped_agent_retention_seconds: float,
    ) -> None:
        self.stream_id = stream_id
        self._retention_ns = int(retention_seconds * 1_000_000_000)
        self._max_events = max_events
        self._max_bytes = max_bytes
        self._max_event_bytes = max_event_bytes
        self._stopped_retention_ns = int(stopped_agent_retention_seconds * 1_000_000_000)
        self._journals: dict[str, _AgentJournal] = {}
        self._lock = asyncio.Lock()

    async def ensure_agent(self, agent_id: str) -> None:
        """Create an agent journal if it does not already exist."""
        async with self._lock:
            journal = self._journals.get(agent_id)
            if journal is None:
                self._journals[agent_id] = self._new_journal(agent_id)
            else:
                journal.stopped_ns = None

    async def mark_stopped(self, agent_id: str) -> None:
        """Mark an agent stopped while preserving its rolling history."""
        async with self._lock:
            journal = self._journals.get(agent_id)
            if journal is not None and journal.stopped_ns is None:
                journal.stopped_ns = time.time_ns()

    async def append(self, *, agent_id: str, instance_id: str, job_id: str | None, payload: bytes) -> EventRecord:
        """Append an opaque event and fan it out to this agent's subscribers."""
        if len(payload) > self._max_event_bytes:
            message = f"Event payload exceeds max size: {len(payload)} > {self._max_event_bytes}."
            sinapsis_logger.error(message)
            raise ValueError(message)

        async with self._lock:
            journal = self._journals.setdefault(agent_id, self._new_journal(agent_id))
            now_ns = time.time_ns()
            record = EventRecord(
                stream_id=self.stream_id,
                cursor=journal.next_cursor,
                created_ns=now_ns,
                agent_id=agent_id,
                instance_id=instance_id,
                job_id=job_id,
                payload=payload,
            )
            journal.next_cursor += 1
            journal.events.append(record)
            journal.size_bytes += record.size_bytes
            journal.prune(now_ns)

            for subscription in tuple(journal.subscriptions.values()):
                if subscription.closed or record.cursor <= subscription.after:
                    continue
                if subscription.job_id is not None and record.job_id != subscription.job_id:
                    continue
                try:
                    subscription.queue.put_nowait(record)
                    subscription.after = record.cursor
                except asyncio.QueueFull:
                    subscription.closed = True
            return record

    async def replay(
        self, *, agent_id: str, after: int, job_id: str | None, limit: int, max_bytes: int
    ) -> ReplayResult:
        """Return retained matching events, clamping an expired cursor to the window."""
        async with self._lock:
            journal = self._require(agent_id)
            journal.prune(time.time_ns())
            return self._replay_locked(journal, after, job_id, limit, max_bytes)

    async def replay_through(
        self,
        *,
        agent_id: str,
        after: int,
        through: int,
        job_id: str | None,
        limit: int,
        max_bytes: int,
    ) -> ReplayResult:
        """Return one replay page capped at a previously captured live boundary."""
        async with self._lock:
            journal = self._require(agent_id)
            journal.prune(time.time_ns())
            return self._replay_locked(journal, after, job_id, limit, max_bytes, through=through)

    async def subscribe(
        self,
        *,
        agent_id: str,
        after: int | None,
        job_id: str | None,
        queue_size: int,
        replay_limit: int,
        replay_max_bytes: int,
    ) -> tuple[int, ReplayResult | None, Subscription]:
        """Atomically establish a subscriber and optional replay boundary.

        ``after=None`` means live-only. Any integer, including zero, means replay
        from that cursor within the retained rolling window and then follow live.
        """
        async with self._lock:
            journal = self._require(agent_id)
            journal.prune(time.time_ns())
            boundary = journal.next_cursor - 1
            replay = None
            if after is not None:
                replay = self._replay_locked(journal, after, job_id, replay_limit, replay_max_bytes, through=boundary)
            subscription = Subscription(queue=asyncio.Queue(maxsize=queue_size), after=boundary, job_id=job_id)
            subscription_id = journal.next_subscription_id
            journal.next_subscription_id += 1
            journal.subscriptions[subscription_id] = subscription
            return subscription_id, replay, subscription

    async def unsubscribe(self, agent_id: str, subscription_id: int) -> None:
        """Remove an ephemeral live subscription."""
        async with self._lock:
            journal = self._journals.get(agent_id)
            if journal is not None:
                journal.subscriptions.pop(subscription_id, None)

    async def bounds(self, agent_id: str) -> JournalWindow:
        """Return the current rolling-window bounds for an agent."""
        async with self._lock:
            journal = self._require(agent_id)
            journal.prune(time.time_ns())
            return journal.window()

    async def purge_expired_stopped_agents(self) -> list[str]:
        """Remove stopped agent journals after their configured grace period."""
        now_ns = time.time_ns()
        removed: list[str] = []
        async with self._lock:
            for agent_id, journal in tuple(self._journals.items()):
                journal.prune(now_ns)
                if journal.stopped_ns is None or journal.subscriptions:
                    continue
                if now_ns - journal.stopped_ns >= self._stopped_retention_ns:
                    self._journals.pop(agent_id, None)
                    removed.append(agent_id)
        return removed

    def _new_journal(self, agent_id: str) -> _AgentJournal:
        return _AgentJournal(
            stream_id=self.stream_id,
            agent_id=agent_id,
            max_events=self._max_events,
            max_bytes=self._max_bytes,
            retention_ns=self._retention_ns,
        )

    def _require(self, agent_id: str) -> _AgentJournal:
        journal = self._journals.get(agent_id)
        if journal is None:
            message = f"Unknown agent event stream: {agent_id}."
            sinapsis_logger.error(message)
            raise KeyError(message)
        return journal

    @staticmethod
    def _replay_locked(
        journal: _AgentJournal,
        after: int,
        job_id: str | None,
        limit: int,
        max_bytes: int,
        through: int | None = None,
    ) -> ReplayResult:
        window = journal.window()
        minimum_after = max(0, window.oldest_cursor - 1)
        effective_after = max(after, minimum_after)
        truncated = after < minimum_after
        selected: list[EventRecord] = []
        selected_bytes = 0
        has_more = False

        for event in journal.events:
            if event.cursor <= effective_after:
                continue
            if through is not None and event.cursor > through:
                break
            if job_id is not None and event.job_id != job_id:
                continue
            if len(selected) >= limit or (selected and selected_bytes + event.size_bytes > max_bytes):
                has_more = True
                break
            selected.append(event)
            selected_bytes += event.size_bytes

        next_cursor = selected[-1].cursor if selected else effective_after
        if not has_more and through is None:
            next_cursor = max(next_cursor, window.latest_cursor)
        elif not has_more and through is not None:
            next_cursor = max(next_cursor, through)

        return ReplayResult(
            events=tuple(selected),
            window=window,
            requested_after=after,
            effective_after=effective_after,
            truncated=truncated,
            has_more=has_more,
            next_cursor=next_cursor,
        )
