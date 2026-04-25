"""CLI command for compacting demo metrics via MetricCompactor."""
import json
import click

from pipewatch.metrics import PipelineMetric, MetricStatus
from pipewatch.compactor import MetricCompactor


def _demo_metrics():
    data = [
        ("ingest", "rows_processed", 1000.0, MetricStatus.OK),
        ("ingest", "rows_processed", 1200.0, MetricStatus.OK),
        ("ingest", "rows_processed", 300.0, MetricStatus.WARNING),
        ("ingest", "error_rate", 0.01, MetricStatus.OK),
        ("transform", "rows_processed", 950.0, MetricStatus.OK),
        ("transform", "rows_processed", 100.0, MetricStatus.CRITICAL),
        ("transform", "latency_ms", 250.0, MetricStatus.WARNING),
    ]
    return [
        PipelineMetric(pipeline=p, name=n, value=v, status=s)
        for p, n, v, s in data
    ]


@click.group(name="compactor")
def compactor_cli():
    """Compact multiple metric snapshots into per-key summaries."""


@compactor_cli.command(name="compact")
@click.option("--pipeline", default=None, help="Filter results to a specific pipeline.")
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]), show_default=True)
def compact_cmd(pipeline: str, fmt: str):
    """Run compaction on demo metrics and display summaries."""
    compactor = MetricCompactor()
    metrics = _demo_metrics()
    results = compactor.compact(metrics)

    if pipeline:
        results = [r for r in results if r.pipeline == pipeline]

    if not results:
        click.echo("No results.")
        return

    if fmt == "json":
        click.echo(json.dumps([r.to_dict() for r in results], indent=2))
    else:
        for r in results:
            click.echo(
                f"[{r.dominant_status.value.upper():8s}] "
                f"{r.pipeline}/{r.name} "
                f"count={r.count} "
                f"min={r.min_value:.2f} max={r.max_value:.2f} mean={r.mean_value:.2f}"
            )
