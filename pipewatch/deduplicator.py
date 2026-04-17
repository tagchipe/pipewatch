"""Deduplication of alerts based on fingerprint and time window."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Optional
from pipewatch.alerts import Alert


@dataclass
class DedupeEntry:
    first_seen: datetime
    last_seen: datetime
    count: int = 1

    def update(self) -> None:
        self.last_seen = datetime.utcnow()
        self.count += 1


class AlertDeduplicator:
    """Suppress duplicate alerts within a rolling time window."""

    def __init__(self, window_seconds: float = 60.0) -> None:
        self.window = timedelta(seconds=window_seconds)
        self._seen: Dict[str, DedupeEntry] = {}

    def _key(self, alert: Alert) -> str:
        return f"{alert.pipeline}:{alert.metric_name}:{alert.status.value}"

    def _prune(self) -> None:
        now = datetime.utcnow()
        self._seen = {
            k: v for k, v in self._seen.items()
            if now - v.last_seen < self.window
        }

    def is_duplicate(self, alert: Alert) -> bool:
        """Return True if alert was already seen within the window."""
        self._prune()
        key = self._key(alert)
        if key in self._seen:
            self._seen[key].update()
            return True
        self._seen[key] = DedupeEntry(
            first_seen=datetime.utcnow(),
            last_seen=datetime.utcnow(),
        )
        return False

    def entry(self, alert: Alert) -> Optional[DedupeEntry]:
        return self._seen.get(self._key(alert))

    def reset(self, alert: Alert) -> None:
        self._seen.pop(self._key(alert), None)

    def clear(self) -> None:
        self._seen.clear()
