"""CLI for pipeline health scoring."""
import click
import json
from datetime import datetime
from pipewatch.metrics import PipelineMetric, MetricStatus
from pipewatch.scorer import PipelineScorer


def _demo_metrics() -> list:
    def m(pipeline, status, name):
        return PipelineMetric(
            name=name, pipeline=pipeline, value=1.0,
            status=status, timestamp=datetime.utcnow()
        )
    return [
        m("ingest", MetricStatus.OK, "row_count"),
        m("ingest", MetricStatus.WARNING, "latency"),
        m("transform", MetricStatus.OK, "row_count"),
        m("transform", MetricStatus.OK, "error_rate"),
        m("load", MetricStatus.CRITICAL, "row_count"),
        m("load", MetricStatus.WARNING, "latency"),
    ]


@click.group(name="scorer")
def scorer_cli():
    """Pipeline health scoring commands."""


@scorer_cli.command(name="score")
@click.option("--pipeline", default=None, help="Filter to a specific pipeline.")
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]))
def score_cmd(pipeline, fmt):
    """Score pipeline health from demo metrics."""
    metrics = _demo_metrics()
    if pipeline:
        metrics = [m for m in metrics if m.pipeline == pipeline]

    scorer = PipelineScorer()
    results = scorer.score_all(metrics)
    results.sort(key=lambda r: r.score)

    if fmt == "json":
        click.echo(json.dumps([r.to_dict() for r in results], indent=2))
        return

    if not results:
        click.echo("No metrics found.")
        return

    click.echo(f"{'Pipeline':<20} {'Score':>7}  {'OK':>4} {'WARN':>4} {'CRIT':>4} {'Total':>6}")
    click.echo("-" * 55)
    for r in results:
        click.echo(
            f"{r.pipeline:<20} {r.score:>6.1f}%  {r.ok:>4} {r.warning:>4} {r.critical:>4} {r.total:>6}"
        )
