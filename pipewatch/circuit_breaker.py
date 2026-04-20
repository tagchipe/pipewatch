"""Circuit breaker for suppressing repeated alerts when a pipeline is consistently failing."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Optional

from pipewatch.metrics import PipelineMetric, MetricStatus


class BreakerState(str, Enum):
    CLOSED = "closed"      # normal — alerts flow through
    OPEN = "open"          # tripped — alerts suppressed
    HALF_OPEN = "half_open"  # probing — one alert allowed through


@dataclass
class BreakerEntry:
    state: BreakerState = BreakerState.CLOSED
    failure_count: int = 0
    opened_at: Optional[datetime] = None
    last_checked: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "opened_at": self.opened_at.isoformat() if self.opened_at else None,
            "last_checked": self.last_checked.isoformat() if self.last_checked else None,
        }


@dataclass
class BreakerResult:
    pipeline: str
    allowed: bool
    state: BreakerState
    failure_count: int

    def to_dict(self) -> dict:
        return {
            "pipeline": self.pipeline,
            "allowed": self.allowed,
            "state": self.state.value,
            "failure_count": self.failure_count,
        }


class CircuitBreaker:
    """Trips open after `threshold` consecutive non-OK metrics; resets after `recovery_seconds`."""

    def __init__(self, threshold: int = 3, recovery_seconds: float = 60.0) -> None:
        self.threshold = threshold
        self.recovery_seconds = recovery_seconds
        self._entries: Dict[str, BreakerEntry] = {}

    def _get(self, pipeline: str) -> BreakerEntry:
        if pipeline not in self._entries:
            self._entries[pipeline] = BreakerEntry()
        return self._entries[pipeline]

    def check(self, metric: PipelineMetric) -> BreakerResult:
        entry = self._get(metric.pipeline)
        now = datetime.utcnow()
        entry.last_checked = now

        # Attempt recovery from OPEN state
        if entry.state == BreakerState.OPEN and entry.opened_at is not None:
            elapsed = (now - entry.opened_at).total_seconds()
            if elapsed >= self.recovery_seconds:
                entry.state = BreakerState.HALF_OPEN

        if metric.status == MetricStatus.OK:
            # Success resets the breaker
            entry.failure_count = 0
            entry.state = BreakerState.CLOSED
            entry.opened_at = None
            return BreakerResult(metric.pipeline, True, entry.state, entry.failure_count)

        # Non-OK metric
        if entry.state == BreakerState.HALF_OPEN:
            # Probe failed — re-open
            entry.state = BreakerState.OPEN
            entry.opened_at = now
            return BreakerResult(metric.pipeline, False, entry.state, entry.failure_count)

        if entry.state == BreakerState.OPEN:
            return BreakerResult(metric.pipeline, False, entry.state, entry.failure_count)

        # CLOSED — accumulate failures
        entry.failure_count += 1
        if entry.failure_count >= self.threshold:
            entry.state = BreakerState.OPEN
            entry.opened_at = now
            return BreakerResult(metric.pipeline, False, entry.state, entry.failure_count)

        return BreakerResult(metric.pipeline, True, entry.state, entry.failure_count)

    def state_for(self, pipeline: str) -> Optional[BreakerEntry]:
        return self._entries.get(pipeline)

    def reset(self, pipeline: str) -> None:
        self._entries.pop(pipeline, None)
