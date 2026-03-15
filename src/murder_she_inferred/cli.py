"""Package-level CLI entrypoints for the pipeline."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


SCRIPT_COMMANDS = {
    "run": "run_full_pipeline.py",
    "chunks": "build_episode_timeline_chunks.py",
    "infer": "infer_timelines_with_codex_cli.py",
    "qc": "qc_timelines.py",
    "plot": "plot_timeline.py",
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _scripts_dir() -> Path:
    return _repo_root() / "scripts"


def _script_path(script_name: str) -> Path:
    path = _scripts_dir() / script_name
    if not path.exists():
        raise FileNotFoundError(f"Script not found: {path}")
    return path


def _run_script(script_name: str, args: list[str]) -> int:
    command = [sys.executable, str(_script_path(script_name)), *args]
    completed = subprocess.run(command, check=False)
    return completed.returncode


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="murder-she-inferred",
        description="Run the murder-she-inferred pipeline or one of its stages.",
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=sorted(SCRIPT_COMMANDS),
        help=(
            "Pipeline command to run. Defaults to 'run' when omitted, so "
            "'murder-she-inferred --run-root test-run' runs the full pipeline."
        ),
    )
    parser.add_argument(
        "args",
        nargs=argparse.REMAINDER,
        help="Arguments passed through to the selected command.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    raw_args = list(sys.argv[1:] if argv is None else argv)
    if not raw_args or raw_args[0].startswith("-"):
        raw_args = ["run", *raw_args]

    parser = _build_parser()
    parsed = parser.parse_args(raw_args)
    command = parsed.command or "run"

    passthrough_args = parsed.args
    if passthrough_args and passthrough_args[0] == "--":
        passthrough_args = passthrough_args[1:]

    return _run_script(SCRIPT_COMMANDS[command], passthrough_args)


if __name__ == "__main__":
    raise SystemExit(main())
