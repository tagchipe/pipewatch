"""Rate-limited notification deduplication for pipewatch alerts."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Dict, Optional

from pipewatch.alerts import Alert


@dataclass
class NotifierConfig:
    cooldown_seconds: float = 60.0
    max_per_minute: int = 10


@dataclass
class _State:
    last_sent: float = 0.0
    count_window_start: float = field(default_factory=time.monotonic)
    count_in_window: int = 0


class Notifier:
    """Wraps an alert handler with deduplication and rate limiting."""

    def __init__(
        self,
        handler: Callable[[Alert], None],
        config: Optional[NotifierConfig] = None,
    ) -> None:
        self._handler = handler
        self._config = config or NotifierConfig()
        self._states: Dict[str, _State] = {}

    def _key(self, alert: Alert) -> str:
        return f"{alert.pipeline}:{alert.metric_name}:{alert.status}"

    def _allowed(self, key: str) -> bool:
        now = time.monotonic()
        state = self._states.setdefault(key, _State(count_window_start=now))

        if now - state.last_sent < self._config.cooldown_seconds:
            return False

        if now - state.count_window_start >= 60.0:
            state.count_window_start = now
            state.count_in_window = 0

        if state.count_in_window >= self._config.max_per_minute:
            return False

        return True

    def send(self, alert: Alert) -> bool:
        """Send alert if rate limits allow. Returns True if sent."""
        key = self._key(alert)
        if not self._allowed(key):
            return False
        state = self._states[key]
        state.last_sent = time.monotonic()
        state.count_in_window += 1
        self._handler(alert)
        return True

    def reset(self, key: Optional[str] = None) -> None:
        """Reset state for a key or all keys."""
        if key is None:
            self._states.clear()
        else:
            self._states.pop(key, None)
