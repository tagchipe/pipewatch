"""Metric collection and threshold evaluation engine."""
from typing import Dict, List, Tuple
from .metrics import PipelineMetric, MetricThreshold, MetricStatus


class MetricCollector:
    """Collects pipeline metrics and evaluates them against thresholds."""

    def __init__(self):
        self._metrics: List[PipelineMetric] = []
        self._thresholds: Dict[str, MetricThreshold] = {}

    def register_threshold(self, threshold: MetricThreshold) -> None:
        """Register a threshold rule for a metric name."""
        self._thresholds[threshold.metric_name] = threshold

    def record(self, metric: PipelineMetric) -> None:
        """Store a metric snapshot."""
        self._metrics.append(metric)

    def evaluate(self, metric: PipelineMetric) -> MetricStatus:
        """Evaluate a metric value against registered thresholds."""
        threshold = self._thresholds.get(metric.metric_name)
        if threshold is None:
            return MetricStatus.UNKNOWN
        return threshold.evaluate(metric.value)

    def get_alerts(self) -> List[Tuple[PipelineMetric, MetricStatus]]:
        """Return all metrics that are in WARNING or CRITICAL state."""
        alerts = []
        for metric in self._metrics:
            status = self.evaluate(metric)
            if status in (MetricStatus.WARNING, MetricStatus.CRITICAL):
                alerts.append((metric, status))
        return alerts

    def summary(self) -> Dict[str, int]:
        """Return a count of metrics by status."""
        counts = {s.value: 0 for s in MetricStatus}
        for metric in self._metrics:
            status = self.evaluate(metric)
            counts[status.value] += 1
        return counts
