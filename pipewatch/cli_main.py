"""Main CLI entry point aggregating all sub-CLIs."""
import click
from pipewatch.cli import cli as report_cli
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
from pipewatch.cli_deduplicator import dedup_cli
from pipewatch.cli_watchdog import watchdog_cli


@click.group()
def main():
    """pipewatch — ETL pipeline health monitor."""


main.add_command(report_cli, name="report")
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
main.add_command(dedup_cli, name="dedup")
main.add_command(watchdog_cli, name="watchdog")


if __name__ == "__main__":
    main()
