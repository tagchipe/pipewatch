import json
import click
from datetime import datetime
from pipewatch.profiler import MetricProfiler
from pipewatch.metrics import PipelineMetric, MetricStatus


def _demo_profiler() -> MetricProfiler:
    profiler = MetricProfiler()
    import random
    random.seed(42)
    for pipeline in ("ingest", "transform"):
        for _ in range(20):
            m = PipelineMetric(
                pipeline=pipeline,
                name="row_count",
                value=random.uniform(800, 1200),
                status=MetricStatus.OK,
                timestamp=datetime.utcnow(),
            )
            profiler.record(m)
    return profiler


@click.group(name="profiler")
def profiler_cli() -> None:
    """Commands for metric value profiling."""


@profiler_cli.command(name="summary")
@click.option("--pipeline", default=None, help="Filter by pipeline name.")
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]), show_default=True)
def summary_cmd(pipeline: str, fmt: str) -> None:
    """Show profiling statistics for recorded metrics."""
    profiler = _demo_profiler()
    entries = [
        e for e in profiler.all_entries()
        if pipeline is None or e.pipeline == pipeline
    ]
    if fmt == "json":
        click.echo(json.dumps([e.to_dict() for e in entries], indent=2))
        return
    if not entries:
        click.echo("No profiling data found.")
        return
    for e in entries:
        click.echo(
            f"[{e.pipeline}] {e.metric_name}: "
            f"n={e.count} mean={e.mean:.2f} "
            f"stddev={e.stddev:.2f if e.stddev is not None else 'N/A'} "
            f"p95={e.p95:.2f if e.p95 is not None else 'N/A'}"
        )
