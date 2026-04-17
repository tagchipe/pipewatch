"""CLI demo for alert deduplication."""
import click
from pipewatch.metrics import PipelineMetric, MetricStatus
from pipewatch.alerts import Alert
from pipewatch.deduplicator import AlertDeduplicator


def _make_alert(name: str, pipeline: str, status: MetricStatus) -> Alert:
    metric = PipelineMetric(name=name, value=0.0, pipeline=pipeline, status=status)
    return Alert(metric=metric, message=f"{name} threshold breached")


@click.group(name="dedup")
def dedup_cli() -> None:
    """Alert deduplication utilities."""


@dedup_cli.command(name="demo")
@click.option("--window", default=5.0, show_default=True, help="Dedup window in seconds.")
@click.option("--repeat", default=3, show_default=True, help="Number of times to fire each alert.")
def demo_cmd(window: float, repeat: int) -> None:
    """Simulate repeated alerts and show deduplication behaviour."""
    dedup = AlertDeduplicator(window_seconds=window)
    alerts = [
        _make_alert("row_count", "etl", MetricStatus.WARNING),
        _make_alert("latency", "ingest", MetricStatus.CRITICAL),
        _make_alert("row_count", "etl", MetricStatus.CRITICAL),
    ]

    for i in range(1, repeat + 1):
        click.echo(f"\n--- Round {i} ---")
        for alert in alerts:
            is_dup = dedup.is_duplicate(alert)
            entry = dedup.entry(alert)
            label = click.style("DUPLICATE", fg="yellow") if is_dup else click.style("NEW", fg="green")
            count = entry.count if entry else 1
            click.echo(
                f"[{label}] {alert.pipeline}/{alert.metric_name} "
                f"({alert.status.value}) — seen {count}x"
            )
