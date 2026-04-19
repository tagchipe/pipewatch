"""Metric ingestion throttler — limits how often a pipeline metric is accepted."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Optional

from pipewatch.metrics import PipelineMetric


@dataclass
class ThrottleResult:
    key: str
    allowed: bool
    next_allowed_at: Optional[datetime]

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "allowed": self.allowed,
            "next_allowed_at": self.next_allowed_at.isoformat() if self.next_allowed_at else None,
        }


@dataclass
class _ThrottleState:
    last_accepted: datetime
    interval: timedelta

    def is_allowed(self, now: datetime) -> bool:
        return now >= self.last_accepted + self.interval

    def next_allowed_at(self) -> datetime:
        return self.last_accepted + self.interval


class MetricThrottler:
    """Accepts a metric at most once per registered interval per pipeline/name key."""

    def __init__(self, default_interval_seconds: float = 60.0) -> None:
        self._default = timedelta(seconds=default_interval_seconds)
        self._intervals: Dict[str, timedelta] = {}
        self._states: Dict[str, _ThrottleState] = {}

    def register(self, pipeline: str, name: str, interval_seconds: float) -> None:
        self._intervals[self._key(pipeline, name)] = timedelta(seconds=interval_seconds)

    def check(self, metric: PipelineMetric) -> ThrottleResult:
        key = self._key(metric.pipeline, metric.name)
        now = datetime.utcnow()
        interval = self._intervals.get(key, self._default)
        state = self._states.get(key)
        if state is None:
            self._states[key] = _ThrottleState(last_accepted=now, interval=interval)
            return ThrottleResult(key=key, allowed=True, next_allowed_at=None)
        if state.is_allowed(now):
            state.last_accepted = now
            return ThrottleResult(key=key, allowed=True, next_allowed_at=None)
        return ThrottleResult(key=key, allowed=False, next_allowed_at=state.next_allowed_at())

    @staticmethod
    def _key(pipeline: str, name: str) -> str:
        return f"{pipeline}::{name}"
