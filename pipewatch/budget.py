"""Metric budget tracking: enforce max allowed violations per pipeline per window."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List
from pipewatch.metrics import PipelineMetric, MetricStatus


@dataclass
class BudgetEntry:
    pipeline: str
    max_violations: int
    window_seconds: float
    _events: List[datetime] = field(default_factory=list, repr=False)

    def _prune(self) -> None:
        cutoff = datetime.utcnow() - timedelta(seconds=self.window_seconds)
        self._events = [e for e in self._events if e >= cutoff]

    def record_violation(self) -> None:
        self._events.append(datetime.utcnow())

    def violation_count(self) -> int:
        self._prune()
        return len(self._events)

    def is_exceeded(self) -> bool:
        return self.violation_count() > self.max_violations


@dataclass
class BudgetResult:
    pipeline: str
    violation_count: int
    max_violations: int
    exceeded: bool

    def to_dict(self) -> dict:
        return {
            "pipeline": self.pipeline,
            "violation_count": self.violation_count,
            "max_violations": self.max_violations,
            "exceeded": self.exceeded,
        }


class BudgetTracker:
    def __init__(self, default_max: int = 5, default_window: float = 3600.0) -> None:
        self._default_max = default_max
        self._default_window = default_window
        self._entries: Dict[str, BudgetEntry] = {}

    def register(self, pipeline: str, max_violations: int, window_seconds: float) -> None:
        self._entries[pipeline] = BudgetEntry(pipeline, max_violations, window_seconds)

    def _get_or_create(self, pipeline: str) -> BudgetEntry:
        if pipeline not in self._entries:
            self._entries[pipeline] = BudgetEntry(
                pipeline, self._default_max, self._default_window
            )
        return self._entries[pipeline]

    def ingest(self, metric: PipelineMetric) -> BudgetResult:
        entry = self._get_or_create(metric.pipeline)
        if metric.status != MetricStatus.OK:
            entry.record_violation()
        return BudgetResult(
            pipeline=metric.pipeline,
            violation_count=entry.violation_count(),
            max_violations=entry.max_violations,
            exceeded=entry.is_exceeded(),
        )

    def check(self, pipeline: str) -> BudgetResult:
        entry = self._get_or_create(pipeline)
        return BudgetResult(
            pipeline=pipeline,
            violation_count=entry.violation_count(),
            max_violations=entry.max_violations,
            exceeded=entry.is_exceeded(),
        )
