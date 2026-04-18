"""CLI for demonstrating retention policy management."""
import json
import click
from datetime import datetime, timedelta
from pipewatch.metrics import PipelineMetric, MetricStatus
from pipewatch.retention import RetentionManager


def _demo_manager() -> tuple[RetentionManager, list]:
    manager = RetentionManager()
    manager.register("ingest", max_age_seconds=3600)
    manager.register("transform", max_age_seconds=300)

    now = datetime.utcnow()
    metrics = [
        PipelineMetric("rows", "ingest", 100.0, MetricStatus.OK, now - timedelta(seconds=100)),
        PipelineMetric("rows", "ingest", 90.0, MetricStatus.OK, now - timedelta(seconds=7200)),
        PipelineMetric("latency", "transform", 0.5, MetricStatus.WARNING, now - timedelta(seconds=50)),
        PipelineMetric("latency", "transform", 1.2, MetricStatus.CRITICAL, now - timedelta(seconds=600)),
    ]
    return manager, metrics


@click.group(name="retention")
def retention_cli():
    """Manage metric retention policies."""


@retention_cli.command(name="apply")
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]))
def apply_cmd(fmt: str):
    """Apply retention policies and report evicted metrics."""
    manager, metrics = _demo_manager()
    result = manager.apply(metrics)

    if fmt == "json":
        click.echo(json.dumps(result.to_dict(), indent=2))
    else:
        click.echo(f"Kept:    {len(result.kept)} metric(s)")
        click.echo(f"Evicted: {len(result.evicted)} metric(s)")
        for m in result.evicted:
            age = (datetime.utcnow() - m.timestamp).total_seconds()
            click.echo(f"  - [{m.pipeline}] {m.name} age={age:.0f}s")
