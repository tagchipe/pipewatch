"""CLI for snapshot capture and diff."""
import json
from datetime import datetime

import click

from pipewatch.metrics import PipelineMetric, MetricStatus
from pipewatch.snapshot import SnapshotManager


def _demo_manager() -> SnapshotManager:
    def _m(pipeline, name, value):
        return PipelineMetric(
            pipeline=pipeline, name=name, value=value,
            status=MetricStatus.OK, timestamp=datetime.utcnow()
        )

    mgr = SnapshotManager()
    mgr.capture("baseline", [
        _m("ingest", "rows_loaded", 1000),
        _m("ingest", "errors", 2),
        _m("transform", "records_out", 980),
    ])
    mgr.capture("current", [
        _m("ingest", "rows_loaded", 1200),
        _m("ingest", "errors", 15),
        _m("transform", "records_out", 980),
        _m("transform", "nulls", 4),
    ])
    return mgr


@click.group(name="snapshot")
def snapshot_cli():
    """Capture and compare metric snapshots."""


@snapshot_cli.command("diff")
@click.option("--before", default="baseline", show_default=True)
@click.option("--after", default="current", show_default=True)
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
def diff_cmd(before, after, fmt):
    """Show delta between two named snapshots."""
    mgr = _demo_manager()
    diffs = mgr.diff(before, after)

    if fmt == "json":
        click.echo(json.dumps([d.to_dict() for d in diffs], indent=2))
        return

    if not diffs:
        click.echo("No diff available.")
        return

    click.echo(f"Diff: {before} → {after}")
    click.echo(f"{'Pipeline':<16} {'Metric':<20} {'Before':>10} {'After':>10} {'Delta':>10}")
    click.echo("-" * 70)
    for d in diffs:
        before_s = f"{d.before:.2f}" if d.before is not None else "N/A"
        after_s = f"{d.after:.2f}" if d.after is not None else "N/A"
        delta_s = f"{d.delta:+.2f}" if d.delta is not None else "N/A"
        click.echo(f"{d.pipeline:<16} {d.metric_name:<20} {before_s:>10} {after_s:>10} {delta_s:>10}")
