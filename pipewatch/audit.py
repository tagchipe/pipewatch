"""Audit log for pipeline metric state transitions."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from pipewatch.metrics import MetricStatus, PipelineMetric


@dataclass
class AuditEntry:
    pipeline: str
    metric_name: str
    previous_status: Optional[MetricStatus]
    current_status: MetricStatus
    value: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "pipeline": self.pipeline,
            "metric_name": self.metric_name,
            "previous_status": self.previous_status.value if self.previous_status else None,
            "current_status": self.current_status.value,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
        }


class AuditLog:
    """Records state transitions for pipeline metrics."""

    def __init__(self, max_entries: int = 500) -> None:
        self._max = max_entries
        self._entries: List[AuditEntry] = []
        self._last_status: dict[str, MetricStatus] = {}

    def _key(self, metric: PipelineMetric) -> str:
        return f"{metric.pipeline}::{metric.name}"

    def record(self, metric: PipelineMetric) -> Optional[AuditEntry]:
        """Record a metric; returns an AuditEntry only on status transition."""
        key = self._key(metric)
        previous = self._last_status.get(key)
        current = metric.status

        if previous == current:
            return None

        entry = AuditEntry(
            pipeline=metric.pipeline,
            metric_name=metric.name,
            previous_status=previous,
            current_status=current,
            value=metric.value,
        )
        self._last_status[key] = current
        self._entries.append(entry)
        if len(self._entries) > self._max:
            self._entries.pop(0)
        return entry

    def entries(self, pipeline: Optional[str] = None) -> List[AuditEntry]:
        if pipeline is None:
            return list(self._entries)
        return [e for e in self._entries if e.pipeline == pipeline]

    def transitions_for(self, pipeline: str, metric_name: str) -> List[AuditEntry]:
        return [
            e for e in self._entries
            if e.pipeline == pipeline and e.metric_name == metric_name
        ]

    def clear(self) -> None:
        self._entries.clear()
        self._last_status.clear()
