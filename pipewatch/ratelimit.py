from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Optional


@dataclass
class RateLimitRule:
    max_calls: int
    window_seconds: float


@dataclass
class _Bucket:
    calls: list = field(default_factory=list)

    def prune(self, window_seconds: float) -> None:
        cutoff = datetime.utcnow() - timedelta(seconds=window_seconds)
        self.calls = [t for t in self.calls if t > cutoff]

    def count(self) -> int:
        return len(self.calls)

    def record(self) -> None:
        self.calls.append(datetime.utcnow())


class RateLimiter:
    """Tracks call rates per key and enforces configurable limits."""

    def __init__(self) -> None:
        self._rules: Dict[str, RateLimitRule] = {}
        self._buckets: Dict[str, _Bucket] = {}

    def register(self, key: str, max_calls: int, window_seconds: float) -> None:
        self._rules[key] = RateLimitRule(max_calls=max_calls, window_seconds=window_seconds)

    def _bucket(self, key: str) -> _Bucket:
        if key not in self._buckets:
            self._buckets[key] = _Bucket()
        return self._buckets[key]

    def is_allowed(self, key: str) -> bool:
        rule = self._rules.get(key)
        if rule is None:
            return True
        bucket = self._bucket(key)
        bucket.prune(rule.window_seconds)
        if bucket.count() < rule.max_calls:
            bucket.record()
            return True
        return False

    def remaining(self, key: str) -> Optional[int]:
        rule = self._rules.get(key)
        if rule is None:
            return None
        bucket = self._bucket(key)
        bucket.prune(rule.window_seconds)
        return max(0, rule.max_calls - bucket.count())

    def reset(self, key: str) -> None:
        self._buckets.pop(key, None)
