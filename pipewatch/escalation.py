from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional
from pipewatch.alerts import Alert


@dataclass
class EscalationLevel:
    level: int
    handler: Callable[[Alert], None]
    after_seconds: float


@dataclass
class EscalationState:
    alert: Alert
    first_seen: datetime = field(default_factory=datetime.utcnow)
    last_escalated_level: int = 0

    def age_seconds(self) -> float:
        return (datetime.utcnow() - self.first_seen).total_seconds()


@dataclass
class EscalationResult:
    alert: Alert
    escalated: bool
    level: int
    reason: str

    def to_dict(self) -> dict:
        return {
            "pipeline": self.alert.pipeline,
            "metric": self.alert.metric_name,
            "escalated": self.escalated,
            "level": self.level,
            "reason": self.reason,
        }


class EscalationManager:
    def __init__(self) -> None:
        self._levels: List[EscalationLevel] = []
        self._states: Dict[str, EscalationState] = {}

    def add_level(self, level: int, handler: Callable[[Alert], None], after_seconds: float) -> None:
        self._levels.append(EscalationLevel(level=level, handler=handler, after_seconds=after_seconds))
        self._levels.sort(key=lambda l: l.level)

    def _key(self, alert: Alert) -> str:
        return f"{alert.pipeline}:{alert.metric_name}"

    def check(self, alert: Alert) -> EscalationResult:
        key = self._key(alert)
        if key not in self._states:
            self._states[key] = EscalationState(alert=alert)
            return EscalationResult(alert=alert, escalated=False, level=0, reason="new alert, tracking started")

        state = self._states[key]
        age = state.age_seconds()

        for lvl in reversed(self._levels):
            if age >= lvl.after_seconds and state.last_escalated_level < lvl.level:
                state.last_escalated_level = lvl.level
                lvl.handler(alert)
                return EscalationResult(alert=alert, escalated=True, level=lvl.level,
                                        reason=f"unresolved for {age:.1f}s, escalated to level {lvl.level}")

        return EscalationResult(alert=alert, escalated=False, level=state.last_escalated_level,
                                reason="within escalation thresholds")

    def resolve(self, alert: Alert) -> None:
        self._states.pop(self._key(alert), None)
