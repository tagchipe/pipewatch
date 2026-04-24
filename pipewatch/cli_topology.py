"""CLI for inspecting pipeline topology."""
from __future__ import annotations

import json
import sys

import click

from pipewatch.topology import TopologyMapper


def _demo_mapper() -> TopologyMapper:
    m = TopologyMapper()
    m.add_edge("ingest_raw", "validate")
    m.add_edge("validate", "transform")
    m.add_edge("transform", "aggregate")
    m.add_edge("aggregate", "load_warehouse")
    m.add_edge("ingest_raw", "audit_log")
    return m


@click.group(name="topology")
def topology_cli() -> None:
    """Inspect pipeline topology and execution order."""


@topology_cli.command(name="order")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
@click.option("--pipeline", default=None, help="Show only a single pipeline node.")
def order_cmd(fmt: str, pipeline: str | None) -> None:
    """Print topological execution order and flag any cycles."""
    mapper = _demo_mapper()
    result = mapper.evaluate()

    if pipeline:
        node = mapper.get(pipeline)
        if node is None:
            click.echo(f"Pipeline '{pipeline}' not found.", err=True)
            sys.exit(1)
        if fmt == "json":
            click.echo(json.dumps(node.to_dict(), indent=2))
        else:
            click.echo(f"Pipeline : {node.name}")
            click.echo(f"Upstream : {', '.join(node.upstream) or '(none)'}")
            click.echo(f"Downstream: {', '.join(node.downstream) or '(none)'}")
        return

    if fmt == "json":
        click.echo(result.to_json())
    else:
        click.echo("Execution order:")
        for i, name in enumerate(result.order, 1):
            click.echo(f"  {i:>2}. {name}")
        if result.has_cycles:
            click.echo("\n[WARNING] Cycles detected:")
            for cycle in result.cycles:
                click.echo(f"  {' -> '.join(cycle)}")
            sys.exit(2)
