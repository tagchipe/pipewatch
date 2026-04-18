"""Unified entry point aggregating all pipewatch CLI groups."""
import click
from pipewatch.cli import cli as report_cli
from pipewatch.cli_summary import summary_cli
from pipewatch.cli_scheduler import scheduler_cli
from pipewatch.cli_exporter import exporter_cli
from pipewatch.cli_tagging import tagging_cli
from pipewatch.cli_baseline import baseline_cli
from pipewatch.cli_anomaly import anomaly_cli
from pipewatch.cli_deduplicator import dedup_cli
from pipewatch.cli_checkpoint import checkpoint_cli
from pipewatch.cli_pipeline_status import pipeline_status_cli
from pipewatch.cli_dependency import dependency_cli


@click.group()
@click.version_option("0.1.0", prog_name="pipewatch")
def main():
    """pipewatch — monitor and alert on ETL pipeline health metrics."""


main.add_command(report_cli, name="report")
main.add_command(summary_cli, name="summary")
main.add_command(scheduler_cli, name="scheduler")
main.add_command(exporter_cli, name="export")
main.add_command(tagging_cli, name="tags")
main.add_command(baseline_cli, name="baseline")
main.add_command(anomaly_cli, name="anomaly")
main.add_command(dedup_cli, name="dedup")
main.add_command(checkpoint_cli, name="checkpoint")
main.add_command(pipeline_status_cli, name="status")
main.add_command(dependency_cli, name="dependency")


if __name__ == "__main__":
    main()
