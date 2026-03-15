"""Shared full-pipeline runner logic."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run chunking, inference, QC, and plotting for a numbered run root.",
    )
    parser.add_argument(
        "--run-root",
        type=Path,
        required=True,
        help="Numbered run root containing 01-transcripts and downstream stage folders.",
    )
    parser.add_argument(
        "--codex-command",
        default="codex exec -",
        help='Shell command used to call Codex CLI during inference. Example: "codex exec -"',
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=None,
        help="Optional fixed chunk size override for continuous-text transcripts.",
    )
    parser.add_argument(
        "--max-chunks",
        type=int,
        default=None,
        help="Optional cap on chunks processed per episode during inference.",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=None,
        help="Optional retries per chunk on invalid inference output.",
    )
    parser.add_argument(
        "--sleep-seconds",
        type=float,
        default=None,
        help="Optional delay between inference chunk calls.",
    )
    parser.add_argument(
        "--max-error-rate",
        type=float,
        default=None,
        help="Optional QC threshold for high error rate flagging.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional max number of episodes to render during plotting.",
    )
    return parser.parse_args(argv)


def _run_step(script_name: str, args: list[str]) -> None:
    command = [sys.executable, str(Path(__file__).resolve().parents[2] / "scripts" / script_name), *args]
    completed = subprocess.run(command, check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    run_root = str(args.run_root)

    build_args = ["--run-root", run_root]
    if args.chunk_size is not None:
        build_args.extend(["--chunk-size", str(args.chunk_size)])
    _run_step("build_episode_timeline_chunks.py", build_args)

    infer_args = [
        "--run-root",
        run_root,
        "--codex-command",
        args.codex_command,
    ]
    if args.max_chunks is not None:
        infer_args.extend(["--max-chunks", str(args.max_chunks)])
    if args.retries is not None:
        infer_args.extend(["--retries", str(args.retries)])
    if args.sleep_seconds is not None:
        infer_args.extend(["--sleep-seconds", str(args.sleep_seconds)])
    _run_step("infer_timelines_with_codex_cli.py", infer_args)

    qc_args = ["--run-root", run_root]
    if args.max_error_rate is not None:
        qc_args.extend(["--max-error-rate", str(args.max_error_rate)])
    _run_step("qc_timelines.py", qc_args)

    plot_args = ["--run-root", run_root]
    if args.limit is not None:
        plot_args.extend(["--limit", str(args.limit)])
    _run_step("plot_timeline.py", plot_args)

    print(f"Full pipeline completed for run root: {args.run_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
