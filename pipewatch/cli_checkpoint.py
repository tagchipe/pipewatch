"""CLI commands for checkpoint and staleness inspection."""
import json
import click
from pipewatch.checkpoint import CheckpointStore
from pipewatch.staleness import StalenessChecker


def _demo_store() -> tuple[CheckpointStore, StalenessChecker]:
    import time
    store = CheckpointStore()
    store.record("etl.sales", metadata={"rows": 5000})
    store.record("etl.users", metadata={"rows": 120})
    checker = StalenessChecker(store)
    checker.register("etl.sales", max_age_seconds=3600)
    checker.register("etl.users", max_age_seconds=3600)
    checker.register("etl.missing", max_age_seconds=60)
    return store, checker


@click.group(name="checkpoint")
def checkpoint_cli():
    """Checkpoint and staleness commands."""


@checkpoint_cli.command(name="list")
@click.option("--fmt", default="text", type=click.Choice(["text", "json"]))
def list_cmd(fmt):
    """List all recorded checkpoints."""
    store, _ = _demo_store()
    entries = store.all()
    if fmt == "json":
        click.echo(json.dumps([e.to_dict() for e in entries], indent=2))
    else:
        for e in entries:
            click.echo(f"{e.pipeline:30s}  age={e.age_seconds():.1f}s  meta={e.metadata}")


@checkpoint_cli.command(name="check-stale")
@click.option("--fmt", default="text", type=click.Choice(["text", "json"]))
@click.option("--only-stale", is_flag=True, default=False)
def check_stale_cmd(fmt, only_stale):
    """Check pipelines for staleness."""
    _, checker = _demo_store()
    results = checker.stale_pipelines() if only_stale else checker.check_all()
    if fmt == "json":
        click.echo(json.dumps([r.to_dict() for r in results], indent=2))
    else:
        for r in results:
            status = "STALE" if r.is_stale else "OK"
            click.echo(f"{r.pipeline:30s}  {status:6s}  age={r.age_seconds:.1f}s / max={r.max_age_seconds}s")
    if any(r.is_stale for r in results):
        raise SystemExit(1)
