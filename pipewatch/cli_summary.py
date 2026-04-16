"""CLI command for displaying aggregated pipeline summaries."""

import click
import json

from pipewatch.aggregator import MetricAggregator
from pipewatch.summary import SummaryBuilder
from pipewatch.cli import _build_demo_collector
from pipewatch.reporter import Reporter


@click.group()
def summary_cli():
    """Pipewatch summary commands."""


@summary_cli.command(name="summary")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.option("--window", default=100, show_default=True, help="Aggregation window size.")
def summary_cmd(as_json: bool, window: int):
    """Show aggregated stats summary for all pipelines."""
    collector = _build_demo_collector()
    collector.evaluate()

    aggregator = MetricAggregator(window_size=window)
    for metric in collector.metrics:
        aggregator.record(metric)

    reporter = Reporter(collector)
    builder = SummaryBuilder(reporter=reporter, aggregator=aggregator)
    summary = builder.build()

    if as_json:
        click.echo(summary.to_json())
    else:
        click.echo(f"Overall Status : {summary.overall_status.value.upper()}")
        click.echo(f"Metrics tracked: {len(summary.report.metrics)}")
        click.echo("")
        for s in summary.stats:
            click.echo(
                f"  [{s.pipeline}] {s.name}: "
                f"mean={s.mean:.2f} min={s.min_val} max={s.max_val} "
                f"n={s.count} status={s.latest_status.value}"
            )


if __name__ == "__main__":
    summary_cli()
