"""Event dispatcher for broadcasting pipeline metric events to registered listeners."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from pipewatch.metrics import PipelineMetric, MetricStatus


Listener = Callable[[PipelineMetric], None]


@dataclass
class DispatchResult:
    metric: PipelineMetric
    listeners_called: int
    skipped: int = 0

    def to_dict(self) -> dict:
        return {
            "pipeline": self.metric.pipeline,
            "metric_name": self.metric.name,
            "status": self.metric.status.value,
            "listeners_called": self.listeners_called,
            "skipped": self.skipped,
        }


class EventDispatcher:
    """Broadcasts PipelineMetric events to registered listeners.

    Listeners can be registered globally or filtered by pipeline name
    and/or MetricStatus.
    """

    def __init__(self) -> None:
        self._listeners: List[tuple] = []  # (listener, pipeline_filter, status_filter)

    def register(
        self,
        listener: Listener,
        *,
        pipeline: Optional[str] = None,
        status: Optional[MetricStatus] = None,
    ) -> Listener:
        """Register a listener, optionally scoped to a pipeline and/or status."""
        self._listeners.append((listener, pipeline, status))
        return listener

    def dispatch(self, metric: PipelineMetric) -> DispatchResult:
        """Send *metric* to all matching listeners and return a DispatchResult."""
        called = 0
        skipped = 0
        for listener, pipeline_filter, status_filter in self._listeners:
            if pipeline_filter is not None and metric.pipeline != pipeline_filter:
                skipped += 1
                continue
            if status_filter is not None and metric.status != status_filter:
                skipped += 1
                continue
            listener(metric)
            called += 1
        return DispatchResult(metric=metric, listeners_called=called, skipped=skipped)

    def listener_count(self) -> int:
        return len(self._listeners)

    def clear(self) -> None:
        """Remove all registered listeners."""
        self._listeners.clear()
