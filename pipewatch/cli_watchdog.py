"""CLI for watchdog: detect dead pipelines."""
import json
import time
from datetime import datetime
import click
from pipewatch.watchdog import Watchdog
from pipewatch.metrics import PipelineMetric, MetricStatus


def _demo_watchdog() -> Watchdog:
    w = Watchdog()
    w.register("ingest", timeout_seconds=5.0)
    w.register("transform", timeout_seconds=5.0)
    w.register("load", timeout_seconds=5.0)
    # simulate 'transform' and 'load' having reported recently
    for pipeline in ("transform", "load"):
        w.record(PipelineMetric(
            name="heartbeat",
            pipeline=pipeline,
            value=1.0,
            status=MetricStatus.OK,
            timestamp=datetime.utcnow(),
        ))
    return w


@click.group(name="watchdog")
def watchdog_cli():
    """Monitor pipeline liveness."""


@watchdog_cli.command(name="check")
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]))
@click.option("--dead-only", is_flag=True, default=False)
def check_cmd(fmt: str, dead_only: bool):
    """Check which pipelines are dead."""
    w = _demo_watchdog()
    results = w.check_all()
    if dead_only:
        results = [r for r in results if r.is_dead]

    if fmt == "json":
        click.echo(json.dumps([r.to_dict() for r in results], indent=2))
        return

    for r in results:
        status = "DEAD" if r.is_dead else "OK"
        seen = r.last_seen.strftime("%H:%M:%S") if r.last_seen else "never"
        click.echo(f"{r.pipeline:<20} {status:<8} last_seen={seen}")
