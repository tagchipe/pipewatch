"""CLI for pipeline dependency health propagation."""
import json
import click
from pipewatch.dependency import DependencyGraph
from pipewatch.metrics import MetricStatus


def _demo_graph() -> tuple[DependencyGraph, dict]:
    g = DependencyGraph()
    g.register("ingest")
    g.register("transform", upstream=["ingest"])
    g.register("load", upstream=["transform"])
    g.register("report", upstream=["load"])
    statuses = {
        "ingest": MetricStatus.OK,
        "transform": MetricStatus.WARNING,
        "load": MetricStatus.OK,
        "report": MetricStatus.OK,
    }
    return g, statuses


@click.group(name="dependency")
def dependency_cli():
    """Pipeline dependency health propagation."""


@dependency_cli.command(name="check")
@click.option("--pipeline", default=None, help="Check a specific pipeline (default: all).")
@click.option("--fmt", default="text", type=click.Choice(["text", "json"]), show_default=True)
def check_cmd(pipeline, fmt):
    """Evaluate propagated health status across dependencies."""
    graph, statuses = _demo_graph()
    targets = [pipeline] if pipeline else graph.pipelines()
    results = [graph.evaluate(p, statuses) for p in targets]

    if fmt == "json":
        click.echo(json.dumps([r.to_dict() for r in results], indent=2))
        return

    for r in results:
        marker = "[BLOCK]" if r.blocking_pipelines else ""
        click.echo(
            f"{r.pipeline:<20} direct={r.direct_status.value:<8} "
            f"propagated={r.propagated_status.value:<8} {marker}"
        )
        if r.blocking_pipelines:
            click.echo(f"  blocked by: {', '.join(r.blocking_pipelines)}")
