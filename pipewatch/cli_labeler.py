"""CLI commands for the metric labeler."""
from __future__ import annotations

import json

import click

from pipewatch.metrics import PipelineMetric, MetricStatus
from pipewatch.labeler import MetricLabeler


def _demo_labeler() -> tuple[MetricLabeler, list[PipelineMetric]]:
    labeler = MetricLabeler()
    metrics = [
        PipelineMetric(name="row_count", pipeline="ingest", value=5000.0, status=MetricStatus.OK),
        PipelineMetric(name="error_rate", pipeline="ingest", value=0.02, status=MetricStatus.WARNING),
        PipelineMetric(name="latency_ms", pipeline="transform", value=320.0, status=MetricStatus.OK),
    ]
    labeler.label(metrics[0], env="prod", team="data-eng")
    labeler.label(metrics[1], env="prod", team="data-eng", severity="high")
    labeler.label(metrics[2], env="staging", team="platform")
    return labeler, metrics


@click.group(name="labeler")
def labeler_cli() -> None:
    """Manage key-value labels on pipeline metrics."""


@labeler_cli.command(name="list")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
def list_cmd(fmt: str) -> None:
    """List all labelled metrics."""
    labeler, _ = _demo_labeler()
    label_sets = labeler.all_label_sets()
    if fmt == "json":
        click.echo(json.dumps([ls.to_dict() for ls in label_sets], indent=2))
        return
    for ls in label_sets:
        label_str = ", ".join(f"{k}={v}" for k, v in ls.labels.items())
        click.echo(f"{ls.pipeline}/{ls.metric_name}  [{label_str}]")


@labeler_cli.command(name="find")
@click.argument("key")
@click.argument("value")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
def find_cmd(key: str, value: str, fmt: str) -> None:
    """Find metrics with a specific label key=value."""
    labeler, _ = _demo_labeler()
    results = labeler.find_by_label(key, value)
    if fmt == "json":
        click.echo(json.dumps([r.to_dict() for r in results], indent=2))
        return
    if not results:
        click.echo(f"No metrics found with {key}={value}")
        return
    for ls in results:
        label_str = ", ".join(f"{k}={v}" for k, v in ls.labels.items())
        click.echo(f"{ls.pipeline}/{ls.metric_name}  [{label_str}]")
