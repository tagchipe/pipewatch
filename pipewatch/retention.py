"""Metric retention policy: evict metrics older than a TTL."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pipewatch.metrics import PipelineMetric


@dataclass
class RetentionPolicy:
    name: str
    max_age_seconds: float

    def is_expired(self, metric: PipelineMetric, now: Optional[datetime] = None) -> bool:
        now = now or datetime.utcnow()
        age = (now - metric.timestamp).total_seconds()
        return age > self.max_age_seconds


@dataclass
class RetentionResult:
    kept: List[PipelineMetric]
    evicted: List[PipelineMetric]

    def to_dict(self) -> dict:
        return {
            "kept": len(self.kept),
            "evicted": len(self.evicted),
        }


class RetentionManager:
    def __init__(self) -> None:
        self._policies: Dict[str, RetentionPolicy] = {}
        self._default_max_age: float = 86400.0  # 24h

    def register(self, pipeline: str, max_age_seconds: float) -> RetentionPolicy:
        policy = RetentionPolicy(name=pipeline, max_age_seconds=max_age_seconds)
        self._policies[pipeline] = policy
        return policy

    def get_policy(self, pipeline: str) -> RetentionPolicy:
        return self._policies.get(
            pipeline,
            RetentionPolicy(name=pipeline, max_age_seconds=self._default_max_age),
        )

    def apply(self, metrics: List[PipelineMetric], now: Optional[datetime] = None) -> RetentionResult:
        kept, evicted = [], []
        for m in metrics:
            policy = self.get_policy(m.pipeline)
            if policy.is_expired(m, now=now):
                evicted.append(m)
            else:
                kept.append(m)
        return RetentionResult(kept=kept, evicted=evicted)
