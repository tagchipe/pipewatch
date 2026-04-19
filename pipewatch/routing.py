"""Alert routing — dispatch alerts to handlers based on pipeline/status rules."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, List, Optional
from pipewatch.alerts import Alert
from pipewatch.metrics import MetricStatus

Handler = Callable[[Alert], None]


@dataclass
class RouteRule:
    handler: Handler
    pipeline: Optional[str] = None
    statuses: Optional[List[MetricStatus]] = None
    name: str = "unnamed"

    def matches(self, alert: Alert) -> bool:
        if self.pipeline and alert.metric.pipeline != self.pipeline:
            return False
        if self.statuses and alert.metric.status not in self.statuses:
            return False
        return True


@dataclass
class RoutingResult:
    alert: Alert
    matched_routes: List[str]
    dispatched: int

    def to_dict(self) -> dict:
        return {
            "metric": alert.metric.name if (alert := self.alert) else None,
            "matched_routes": self.matched_routes,
            "dispatched": self.dispatched,
        }


class AlertRouter:
    def __init__(self) -> None:
        self._rules: List[RouteRule] = []

    def add_route(
        self,
        handler: Handler,
        *,
        pipeline: Optional[str] = None,
        statuses: Optional[List[MetricStatus]] = None,
        name: str = "unnamed",
    ) -> RouteRule:
        rule = RouteRule(handler=handler, pipeline=pipeline, statuses=statuses, name=name)
        self._rules.append(rule)
        return rule

    def dispatch(self, alert: Alert) -> RoutingResult:
        matched: List[str] = []
        count = 0
        for rule in self._rules:
            if rule.matches(alert):
                rule.handler(alert)
                matched.append(rule.name)
                count += 1
        return RoutingResult(alert=alert, matched_routes=matched, dispatched=count)

    def route_names(self) -> List[str]:
        return [r.name for r in self._rules]
