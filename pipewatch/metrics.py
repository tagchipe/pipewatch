"""Core metric models for pipeline health tracking."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class MetricStatus(Enum):
    OK = "ok"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class PipelineMetric:
    """Represents a single pipeline health metric snapshot."""
    pipeline_id: str
    metric_name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    unit: Optional[str] = None
    tags: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "pipeline_id": self.pipeline_id,
            "metric_name": self.metric_name,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "unit": self.unit,
            "tags": self.tags,
        }


@dataclass
class MetricThreshold:
    """Defines warning and critical thresholds for a metric."""
    metric_name: str
    warning: float
    critical: float
    comparison: str = "gt"  # 'gt' or 'lt'

    def evaluate(self, value: float) -> MetricStatus:
        def exceeds(v, threshold):
            return v > threshold if self.comparison == "gt" else v < threshold

        if exceeds(value, self.critical):
            return MetricStatus.CRITICAL
        if exceeds(value, self.warning):
            return MetricStatus.WARNING
        return MetricStatus.OK
