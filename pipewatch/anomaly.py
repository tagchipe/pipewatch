from dataclasses import dataclass, field
from typing import List, Optional
from pipewatch.metrics import PipelineMetric
from pipewatch.history import MetricHistory


@dataclass
class AnomalyResult:
    metric_name: str
    pipeline: str
    value: float
    mean: float
    stddev: float
    z_score: float
    is_anomaly: bool

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "pipeline": self.pipeline,
            "value": self.value,
            "mean": round(self.mean, 4),
            "stddev": round(self.stddev, 4),
            "z_score": round(self.z_score, 4),
            "is_anomaly": self.is_anomaly,
        }


class AnomalyDetector:
    def __init__(self, threshold: float = 2.0, min_samples: int = 3):
        self.threshold = threshold
        self.min_samples = min_samples
        self._histories: dict[str, MetricHistory] = {}

    def _key(self, metric: PipelineMetric) -> str:
        return f"{metric.pipeline}::{metric.name}"

    def record(self, metric: PipelineMetric) -> None:
        key = self._key(metric)
        if key not in self._histories:
            self._histories[key] = MetricHistory(max_size=100)
        self._histories[key].add(metric)

    def check(self, metric: PipelineMetric) -> Optional[AnomalyResult]:
        key = self._key(metric)
        history = self._histories.get(key)
        if history is None:
            return None
        vals = history.values()
        if len(vals) < self.min_samples:
            return None
        mean = sum(vals) / len(vals)
        variance = sum((v - mean) ** 2 for v in vals) / len(vals)
        stddev = variance ** 0.5
        if stddev == 0:
            z_score = 0.0
        else:
            z_score = abs(metric.value - mean) / stddev
        return AnomalyResult(
            metric_name=metric.name,
            pipeline=metric.pipeline,
            value=metric.value,
            mean=mean,
            stddev=stddev,
            z_score=z_score,
            is_anomaly=z_score > self.threshold,
        )

    def record_and_check(self, metric: PipelineMetric) -> Optional[AnomalyResult]:
        result = self.check(metric)
        self.record(metric)
        return result
