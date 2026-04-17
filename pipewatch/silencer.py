"""Silence (suppress) alerts for specific metrics or pipelines for a duration."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Optional

from pipewatch.alerts import Alert


@dataclass
class SilenceRule:
    key: str  # metric name or pipeline name
    expires_at: datetime
    reason: str = ""

    def is_active(self, now: Optional[datetime] = None) -> bool:
        now = now or datetime.utcnow()
        return now < self.expires_at


@dataclass
class Silencer:
    _rules: Dict[str, SilenceRule] = field(default_factory=dict)

    def silence(self, key: str, duration_seconds: int, reason: str = "") -> SilenceRule:
        """Add or replace a silence rule for *key*."""
        rule = SilenceRule(
            key=key,
            expires_at=datetime.utcnow() + timedelta(seconds=duration_seconds),
            reason=reason,
        )
        self._rules[key] = rule
        return rule

    def is_silenced(self, key: str, now: Optional[datetime] = None) -> bool:
        rule = self._rules.get(key)
        if rule is None:
            return False
        if rule.is_active(now):
            return True
        # expired — clean up
        del self._rules[key]
        return False

    def allow(self, alert: Alert, now: Optional[datetime] = None) -> bool:
        """Return True if the alert should be forwarded (not silenced)."""
        return not self.is_silenced(alert.metric.name, now) and not self.is_silenced(
            alert.metric.pipeline, now
        )

    def active_rules(self) -> list[SilenceRule]:
        now = datetime.utcnow()
        return [r for r in self._rules.values() if r.is_active(now)]

    def clear(self, key: str) -> bool:
        """Remove a silence rule. Returns True if it existed."""
        return self._rules.pop(key, None) is not None
