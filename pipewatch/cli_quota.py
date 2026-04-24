"""CLI commands for demonstrating quota enforcement."""
from __future__ import annotations

import json
import time

import click

from pipewatch.metrics import PipelineMetric, MetricStatus
from pipewatch.quota import QuotaManager


def _demo_manager() -> QuotaManager:
    mgr = QuotaManager(default_limit=5, default_window=60)
    mgr.register("orders", limit=3, window_seconds=60)
    return mgr


def _demo_metrics() -> list:
    now = time.time()
    return [
        PipelineMetric("row_count", "orders", float(i), MetricStatus.OK, now)
        for i in range(5)
    ]


@click.group(name="quota")
def quota_cli() -> None:
    """Quota enforcement commands."""


@quota_cli.command(name="demo")
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]))
def demo_cmd(fmt: str) -> None:
    """Run a quota demo showing accepted and blocked metrics."""
    mgr = _demo_manager()
    metrics = _demo_metrics()
    results = [mgr.check(m) for m in metrics]

    if fmt == "json":
        click.echo(json.dumps([r.to_dict() for r in results], indent=2))
        return

    for r in results:
        status = "ACCEPTED" if r.accepted else "BLOCKED "
        click.echo(
            f"[{status}] pipeline={r.pipeline}  used={r.used}/{r.limit}  "
            f"window={r.window_seconds}s"
        )
