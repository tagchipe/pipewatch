"""Alert handlers for pipeline metric threshold violations."""

from dataclasses import dataclass, field
from typing import Callable, List, Optional
from datetime import datetime

from pipewatch.metrics import PipelineMetric, MetricStatus


@dataclass
class Alert:
    """Represents a triggered alert for a metric violation."""
    pipeline: str
    metric_name: str
    status: MetricStatus
    value: float
    message: str
    triggered_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "pipeline": self.pipeline,
            "metric_name": self.metric_name,
            "status": self.status.value,
            "value": self.value,
            "message": self.message,
            "triggered_at": self.triggered_at.isoformat(),
        }


AlertHandler = Callable[[Alert], None]


class AlertManager:
    """Manages alert handlers and dispatches alerts based on metric evaluations."""

    def __init__(self) -> None:
        self._handlers: List[AlertHandler] = []
        self._history: List[Alert] = []

    def register_handler(self, handler: AlertHandler) -> None:
        """Register a callable that receives Alert objects."""
        self._handlers.append(handler)

    def evaluate_and_alert(self, metric: PipelineMetric, status: MetricStatus) -> Optional[Alert]:
        """Create and dispatch an alert if status is not OK."""
        if status == MetricStatus.OK:
            return None

        alert = Alert(
            pipeline=metric.pipeline,
            metric_name=metric.name,
            status=status,
            value=metric.value,
            message=(
                f"[{status.value.upper()}] {metric.pipeline}/{metric.name} "
                f"= {metric.value} (at {metric.collected_at.isoformat()})"
            ),
        )
        self._history.append(alert)
        for handler in self._handlers:
            handler(alert)
        return alert

    @property
    def history(self) -> List[Alert]:
        return list(self._history)

    def clear_history(self) -> None:
        self._history.clear()
