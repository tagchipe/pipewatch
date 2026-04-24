"""Main CLI entry point aggregating all sub-commands."""
from __future__ import annotations

import click

from pipewatch.cli import cli
from pipewatch.cli_summary import summary_cli
from pipewatch.cli_scheduler import scheduler_cli
from pipewatch.cli_exporter import exporter_cli
from pipewatch.cli_tagging import tagging_cli
from pipewatch.cli_baseline import baseline_cli
from pipewatch.cli_anomaly import anomaly_cli
from pipewatch.cli_checkpoint import checkpoint_cli
from pipewatch.cli_pipeline_status import pipeline_status_cli
from pipewatch.cli_dependency import dependency_cli
from pipewatch.cli_retention import retention_cli
from pipewatch.cli_snapshot import snapshot_cli
from pipewatch.cli_watchdog import watchdog_cli
from pipewatch.cli_throttle import throttle_cli
from pipewatch.cli_scorer import scorer_cli
from pipewatch.cli_budget import budget_cli
from pipewatch.cli_profiler import profiler_cli
from pipewatch.cli_routing import routing_cli
from pipewatch.cli_circuit_breaker import circuit_breaker_cli
from pipewatch.cli_deduplicator import dedup_cli
from pipewatch.cli_topology import topology_cli
from pipewatch.cli_quota import quota_cli


@click.group()
def main() -> None:
    """pipewatch — ETL pipeline health monitoring CLI."""


main.add_command(cli, name="report")
main.add_command(summary_cli, name="summary")
main.add_command(scheduler_cli, name="scheduler")
main.add_command(exporter_cli, name="export")
main.add_command(tagging_cli, name="tags")
main.add_command(baseline_cli, name="baseline")
main.add_command(anomaly_cli, name="anomaly")
main.add_command(checkpoint_cli, name="checkpoint")
main.add_command(pipeline_status_cli, name="status")
main.add_command(dependency_cli, name="deps")
main.add_command(retention_cli, name="retention")
main.add_command(snapshot_cli, name="snapshot")
main.add_command(watchdog_cli, name="watchdog")
main.add_command(throttle_cli, name="throttle")
main.add_command(scorer_cli, name="score")
main.add_command(budget_cli, name="budget")
main.add_command(profiler_cli, name="profiler")
main.add_command(routing_cli, name="routing")
main.add_command(circuit_breaker_cli, name="breaker")
main.add_command(dedup_cli, name="dedup")
main.add_command(topology_cli, name="topology")
main.add_command(quota_cli, name="quota")
