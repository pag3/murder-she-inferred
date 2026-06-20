#!/usr/bin/env python3
"""Infer suspect timelines from chunk files using Codex CLI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from murder_she_inferred.backends import codex_cli_backend
from murder_she_inferred.inference import build_timeline
from murder_she_inferred.settings import get_data_dir, run_stage_path


def parse_args() -> argparse.Namespace:
    data_dir = get_data_dir(must_exist=False)
    default_input_dir = data_dir / "episode_timeline_chunks"
    default_output_dir = data_dir / "episode_timelines_codex_cli"

    parser = argparse.ArgumentParser(
        description="Run Codex CLI per chunk and build timeline output files.",
    )
    parser.add_argument(
        "--run-root",
        type=Path,
        default=None,
        help="Optional numbered run root. Uses 02-chunks and 03-timelines under this root.",
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=None,
        help=f"Directory containing *.chunks.json files (default: {default_input_dir})",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help=f"Directory to write *.timeline.json files (default: {default_output_dir})",
    )
    parser.add_argument(
        "--file",
        type=Path,
        default=None,
        help="Optional single *.chunks.json file to process.",
    )
    parser.add_argument(
        "--codex-command",
        default="codex exec -",
        help=(
            "Shell command used to call Codex CLI. Prompt is sent on stdin. "
            "Example: \"codex exec -\""
        ),
    )
    parser.add_argument(
        "--max-chunks",
        type=int,
        default=None,
        help="Optional cap on chunks processed per episode (for quick experiments).",
    )
    parser.add_argument(
        "--context-window",
        type=int,
        default=5,
        help=(
            "Number of recent chunks to include as raw transcript context "
            "in each prompt (default: 5). Earlier chunks are represented "
            "only by the structured prior state summary. Use 0 for full "
            "cumulative context (all prior chunks)."
        ),
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=2,
        help="Retries per chunk on invalid output (default: 2).",
    )
    parser.add_argument(
        "--sleep-seconds",
        type=float,
        default=0.0,
        help="Optional delay between chunk calls.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    default_data_dir = get_data_dir(must_exist=False)
    input_dir = (
        args.input_dir
        or (run_stage_path(args.run_root, "chunks") if args.run_root else None)
        or (default_data_dir / "episode_timeline_chunks")
    )
    output_dir = (
        args.output_dir
        or (run_stage_path(args.run_root, "timelines") if args.run_root else None)
        or (default_data_dir / "episode_timelines_codex_cli")
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
    total_files = len(files)
    for path in files:
        print(f"[{processed + 1}/{total_files}] {path.stem}", flush=True)
        payload = json.loads(path.read_text(encoding="utf-8"))

        backend_fn = codex_cli_backend(args.codex_command)

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
