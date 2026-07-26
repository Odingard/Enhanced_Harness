"""Enhanced Harness CLI — `harness`."""

from __future__ import annotations

import json
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import typer

from enhanced_harness import __version__
from enhanced_harness.agents.conductor import run_session_sync
from enhanced_harness.config import DEFAULT_OUT_ROOT, PRODUCT_NAME
from enhanced_harness.modules.base import list_modules
from enhanced_harness.safety import doctor_checks
from enhanced_harness.scope import load_scope
from enhanced_harness.skills.loader import load_registry

app = typer.Typer(
    name="harness",
    help=f"{PRODUCT_NAME} — Shannon-class multi-agent red team for Agentic AI / MCP",
    add_completion=False,
    no_args_is_help=True,
)


def _latest_session(out_root: Path) -> Path | None:
    if not out_root.exists():
        return None
    sessions = [p for p in out_root.iterdir() if p.is_dir()]
    if not sessions:
        return None
    return sorted(sessions, key=lambda p: p.stat().st_mtime, reverse=True)[0]


def _resolve_out(out: Optional[Path]) -> Path:
    if out is not None:
        return out
    latest = _latest_session(DEFAULT_OUT_ROOT)
    if latest is None:
        raise typer.BadParameter("No session output found; pass --out DIR")
    return latest


@app.command()
def setup() -> None:
    """Create local scaffolding (out dir, example scope, kill-switch path)."""
    DEFAULT_OUT_ROOT.mkdir(parents=True, exist_ok=True)
    example_src = Path("scope.example.json")
    example_dst = Path("scope.json")
    if example_src.exists() and not example_dst.exists():
        shutil.copy(example_src, example_dst)
        typer.echo(f"Wrote {example_dst} from scope.example.json")
    else:
        typer.echo("scope.json already present or scope.example.json missing — skipped copy")
    typer.echo(f"Output root: {DEFAULT_OUT_ROOT.resolve()}")
    typer.echo("Next: edit scope.json, then run `harness doctor --scope scope.json`")


@app.command()
def doctor(
    scope: Path = typer.Option(..., "--scope", exists=True, readable=True),
) -> None:
    """Validate scope / ROE / allowlist / budgets (fail closed)."""
    try:
        sc = load_scope(scope)
    except Exception as e:  # noqa: BLE001
        typer.secho(f"FAIL: scope invalid: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=2) from e
    issues = doctor_checks(sc)
    fatal = [i for i in issues if not i.startswith("warning:")]
    warnings = [i for i in issues if i.startswith("warning:")]
    for w in warnings:
        typer.secho(w, fg=typer.colors.YELLOW)
    if fatal:
        for i in fatal:
            typer.secho(f"FAIL: {i}", fg=typer.colors.RED)
        raise typer.Exit(code=2)
    # Skills registry load check
    reg = load_registry()
    typer.echo(f"OK: scope valid; {len(reg.skills)} skills loaded; modules={sc.modules_enabled}")


@app.command("start")
def start(
    scope: Path = typer.Option(..., "--scope", exists=True, readable=True),
    out: Optional[Path] = typer.Option(None, "--out", help="Session output directory"),
) -> None:
    """Start a multi-agent engagement session."""
    sc = load_scope(scope)
    issues = [i for i in doctor_checks(sc) if not i.startswith("warning:")]
    if issues:
        for i in issues:
            typer.secho(f"FAIL: {i}", fg=typer.colors.RED)
        raise typer.Exit(code=2)

    if out is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out = DEFAULT_OUT_ROOT / f"session-{stamp}"
    out.mkdir(parents=True, exist_ok=True)

    typer.echo(f"Starting {PRODUCT_NAME} → {out}")
    run_session_sync(sc, out)
    findings = out / "findings.json"
    if findings.exists():
        data = json.loads(findings.read_text(encoding="utf-8"))
        confirmed = sum(1 for f in data if f.get("status") == "confirmed")
        typer.echo(f"Done. Confirmed findings: {confirmed}. Report: {out / 'findings.md'}")
    else:
        typer.echo(f"Done. Output: {out}")


@app.command("engage")
def engage(
    scope: Path = typer.Option(..., "--scope", exists=True, readable=True),
    out: Optional[Path] = typer.Option(None, "--out"),
) -> None:
    """Alias for `harness start`."""
    start(scope=scope, out=out)


@app.command()
def logs(
    out: Optional[Path] = typer.Option(None, "--out"),
    follow: bool = typer.Option(False, "--follow", "-f"),
) -> None:
    """Show harness.log for a session."""
    session = _resolve_out(out)
    log_path = session / "harness.log"
    if not log_path.exists():
        typer.secho(f"No harness.log in {session}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    if not follow:
        typer.echo(log_path.read_text(encoding="utf-8"), nl=False)
        return
    with log_path.open("r", encoding="utf-8") as f:
        f.seek(0, 2)
        try:
            while True:
                line = f.readline()
                if line:
                    typer.echo(line, nl=False)
                else:
                    time.sleep(0.25)
        except KeyboardInterrupt:
            raise typer.Exit(code=0) from None


@app.command()
def resume(
    out: Path = typer.Option(..., "--out", exists=True, file_okay=False),
) -> None:
    """Resume is limited in Milestone 1 — re-runs from scope.used.json if present."""
    used = out / "scope.used.json"
    if not used.exists():
        typer.secho("scope.used.json missing; cannot resume", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    new_out = out.parent / f"session-{stamp}-resume"
    typer.echo(f"Milestone 1 resume = fresh run from prior scope → {new_out}")
    start(scope=used, out=new_out)


@app.command()
def report(
    out: Optional[Path] = typer.Option(None, "--out"),
) -> None:
    """Print findings.md / summary for a session."""
    session = _resolve_out(out)
    md = session / "findings.md"
    js = session / "findings.json"
    if md.exists():
        typer.echo(md.read_text(encoding="utf-8"))
    elif js.exists():
        typer.echo(js.read_text(encoding="utf-8"))
    else:
        typer.secho(f"No findings in {session}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


@app.command()
def modules() -> None:
    """List attack modules available in this build."""
    for m in list_modules():
        typer.echo(f"{m['id']}\t{m['name']}\t[{m['surfaces']}]")
    reg = load_registry()
    typer.echo("")
    typer.echo("Skills:")
    for s in reg.skills.values():
        typer.echo(f"  {s.id}\tmodule={s.module}\tsurfaces={','.join(s.surfaces)}")


@app.command()
def version() -> None:
    """Print version."""
    typer.echo(f"{PRODUCT_NAME} {__version__}")
    typer.echo("CLI: harness")
    typer.echo("Package: enhanced_harness")


# Typer app callable for console_scripts
def main() -> None:
    app()


if __name__ == "__main__":
    main()
