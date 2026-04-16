"""CLI entry point for pipewatch."""
import json
import sys

import click

from pipewatch.alerts import AlertManager
from pipewatch.collector import MetricCollector
from pipewatch.handlers import console_handler, FileHandler
from pipewatch.reporter import Reporter


def _build_demo_collector() -> MetricCollector:
    """Build a sample collector for demo/testing purposes."""
    from pipewatch.metrics import MetricThreshold, MetricStatus, PipelineMetric
    import time

    collector = MetricCollector()
    collector.register_threshold("row_count", MetricThreshold(warning=100, critical=10))
    collector.register_threshold("latency_ms", MetricThreshold(warning=500, critical=2000))
    collector.record(PipelineMetric(name="row_count", value=85, timestamp=time.time()))
    collector.record(PipelineMetric(name="latency_ms", value=1800, timestamp=time.time()))
    return collector


@click.group()
def cli():
    """pipewatch — ETL pipeline health monitor."""


@cli.command("report")
@click.option("--pipeline", default="default", help="Pipeline name label.")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
@click.option("--output", default=None, help="Write report to file path.")
def report_cmd(pipeline: str, fmt: str, output):
    """Generate a pipeline health report."""
    collector = _build_demo_collector()
    reporter = Reporter(collector, pipeline_name=pipeline)
    rep = reporter.generate()

    if fmt == "json":
        content = rep.to_json()
    else:
        lines = [f"Pipeline: {rep.pipeline_name}", f"Status:   {rep.overall_status}",
                 f"Generated: {rep.generated_at}", "-" * 40]
        for m in rep.metrics:
            lines.append(f"  {m['name']}: {m['value']} [{m['status']}]")
        content = "\n".join(lines)

    if output:
        with open(output, "w") as f:
            f.write(content)
        click.echo(f"Report written to {output}")
    else:
        click.echo(content)

    if rep.overall_status == "critical":
        sys.exit(2)
    elif rep.overall_status == "warning":
        sys.exit(1)


if __name__ == "__main__":
    cli()
