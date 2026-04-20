"""CLI for demonstrating the circuit breaker."""
from __future__ import annotations

import json
from datetime import datetime

import click

from pipewatch.metrics import PipelineMetric, MetricStatus
from pipewatch.circuit_breaker import CircuitBreaker


def _demo_breaker() -> CircuitBreaker:
    return CircuitBreaker(threshold=3, recovery_seconds=60.0)


def _demo_sequence() -> list[tuple[str, MetricStatus]]:
    return [
        ("ingest", MetricStatus.OK),
        ("ingest", MetricStatus.WARNING),
        ("ingest", MetricStatus.CRITICAL),
        ("ingest", MetricStatus.CRITICAL),
        ("ingest", MetricStatus.CRITICAL),   # trips open here
        ("ingest", MetricStatus.CRITICAL),   # blocked
        ("transform", MetricStatus.WARNING),
        ("transform", MetricStatus.OK),
    ]


@click.group(name="circuit-breaker")
def circuit_breaker_cli() -> None:
    """Circuit breaker commands."""


@circuit_breaker_cli.command(name="demo")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
def demo_cmd(fmt: str) -> None:
    """Run a demo sequence through the circuit breaker."""
    breaker = _demo_breaker()
    results = []
    for pipeline, status in _demo_sequence():
        metric = PipelineMetric(
            name="row_count",
            pipeline=pipeline,
            value=100.0,
            status=status,
            timestamp=datetime.utcnow(),
        )
        result = breaker.check(metric)
        results.append(result)

    if fmt == "json":
        click.echo(json.dumps([r.to_dict() for r in results], indent=2))
    else:
        for r in results:
            allowed_label = "ALLOWED" if r.allowed else "BLOCKED"
            click.echo(
                f"[{r.pipeline}] status={r.state.value} "
                f"failures={r.failure_count} -> {allowed_label}"
            )
