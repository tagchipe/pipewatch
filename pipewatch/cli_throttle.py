"""CLI demo for the metric throttler."""
import json
import click

from pipewatch.metrics import PipelineMetric, MetricStatus
from pipewatch.throttle import MetricThrottler


def _demo_throttler() -> MetricThrottler:
    t = MetricThrottler(default_interval_seconds=60.0)
    t.register("payments", "row_count", interval_seconds=30.0)
    return t


@click.group(name="throttle")
def throttle_cli():
    """Metric ingestion throttle controls."""


@throttle_cli.command(name="check")
@click.option("--pipeline", default="payments", show_default=True)
@click.option("--metric", "name", default="row_count", show_default=True)
@click.option("--value", default=100.0, type=float, show_default=True)
@click.option("--repeat", default=2, type=int, show_default=True, help="How many times to submit.")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text", show_default=True)
def check_cmd(pipeline: str, name: str, value: float, repeat: int, fmt: str):
    """Submit a metric N times and show throttle decisions."""
    throttler = _demo_throttler()
    metric = PipelineMetric(pipeline=pipeline, name=name, value=value, status=MetricStatus.OK)
    results = [throttler.check(metric) for _ in range(repeat)]

    if fmt == "json":
        click.echo(json.dumps([r.to_dict() for r in results], indent=2))
    else:
        for r in results:
            status = "ALLOWED" if r.allowed else "BLOCKED"
            nxt = r.next_allowed_at.isoformat() if r.next_allowed_at else "-"
            click.echo(f"[{status}] key={r.key}  next_allowed={nxt}")
