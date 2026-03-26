#!/usr/bin/env python3
"""Infer suspect timelines using a configurable LLM backend."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from murder_she_inferred.backends import codex_cli_backend, openai_http_backend
from murder_she_inferred.inference import build_timeline
from murder_she_inferred.settings import get_data_dir, run_stage_path


def parse_args() -> argparse.Namespace:
    data_dir = get_data_dir(must_exist=False)
    default_input_dir = data_dir / "episode_timeline_chunks"
    default_output_dir = data_dir / "episode_timelines"

    parser = argparse.ArgumentParser(
        description="Run LLM inference per chunk and build timeline output files.",
    )
    parser.add_argument(
        "--backend",
        choices=["codex-cli", "local"],
        default="codex-cli",
        help="Inference backend to use (default: codex-cli).",
    )

    # Backend-specific options
    parser.add_argument(
        "--codex-command",
        default="codex exec -",
        help="Shell command for Codex CLI backend. Prompt sent on stdin (default: 'codex exec -').",
    )
    parser.add_argument(
        "--api-url",
        default="http://localhost:11434/v1/chat/completions",
        help="URL for local backend's OpenAI-compatible endpoint (default: Ollama's default).",
    )
    parser.add_argument(
        "--model",
        default="llama3",
        help="Model name for local backend (default: llama3).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=120.0,
        help="HTTP request timeout in seconds for local backend (default: 120).",
    )

    # Shared options (same as existing script)
    parser.add_argument("--run-root", type=Path, default=None,
        help="Optional numbered run root. Uses 02-chunks and 03-timelines under this root.")
    parser.add_argument("--input-dir", type=Path, default=None,
        help=f"Directory containing *.chunks.json files (default: {default_input_dir})")
    parser.add_argument("--output-dir", type=Path, default=None,
        help=f"Directory to write *.timeline.json files (default: {default_output_dir})")
    parser.add_argument("--file", type=Path, default=None,
        help="Optional single *.chunks.json file to process.")
    parser.add_argument("--max-chunks", type=int, default=None,
        help="Optional cap on chunks processed per episode.")
    parser.add_argument("--context-window", type=int, default=5,
        help="Number of recent chunks as transcript context (default: 5). Use 0 for full cumulative.")
    parser.add_argument("--retries", type=int, default=2,
        help="Retries per chunk on invalid output (default: 2).")
    parser.add_argument("--sleep-seconds", type=float, default=0.0,
        help="Optional delay between chunk calls.")

    return parser.parse_args()


def _make_backend(args: argparse.Namespace):
    """Create the backend callable based on --backend flag."""
    if args.backend == "local":
        return openai_http_backend(
            api_url=args.api_url,
            model=args.model,
            timeout=args.timeout,
        )
    return codex_cli_backend(args.codex_command)


def main() -> int:
    args = parse_args()
    backend_fn = _make_backend(args)

    default_data_dir = get_data_dir(must_exist=False)
    input_dir = (
        args.input_dir
        or (run_stage_path(args.run_root, "chunks") if args.run_root else None)
        or (default_data_dir / "episode_timeline_chunks")
    )
    output_dir = (
        args.output_dir
        or (run_stage_path(args.run_root, "timelines") if args.run_root else None)
        or (default_data_dir / "episode_timelines")
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.file is not None:
        files = [args.file]
    else:
        files = sorted(input_dir.glob("*.chunks.json"))

    if not files:
        if args.run_root and args.input_dir is None and args.file is None:
            raise FileNotFoundError(
                f"No input chunk files found in: {input_dir}\n"
                "Expected numbered input folder 02-chunks under the run root."
            )
        raise FileNotFoundError("No input chunk files found.")

    processed = 0
    for path in files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        timeline_payload = build_timeline(
            payload,
            backend_fn=backend_fn,
            max_chunks=args.max_chunks,
            context_window=args.context_window,
            retries=args.retries,
            sleep_seconds=args.sleep_seconds,
        )
        output_path = output_dir / f"{path.stem.replace('.chunks', '')}.timeline.json"
        output_path.write_text(
            json.dumps(timeline_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        processed += 1

    print(f"Processed episodes: {processed}")
    print(f"Output directory: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
