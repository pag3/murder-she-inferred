#!/usr/bin/env python3
"""Build chunked episode timeline files from local transcripts."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from murder_she_inferred.ingest import (
    DEFAULT_CHUNK_SIZE,
    split_into_chunks,
    strip_boilerplate,
)
from murder_she_inferred.settings import get_data_dir, run_stage_path

_SLUG_LINE_RE = re.compile(
    r"^\s*(?:INT\.|EXT\.|INT\./EXT\.|EXT\./INT\.|INT/EXT|I/E\.)\s",
    re.IGNORECASE | re.MULTILINE,
)


def choose_mode(text: str) -> str:
    """Pick a chunk mode based on transcript structure."""
    if _SLUG_LINE_RE.search(text):
        return "scene"
    return "fixed"


def build_one(transcript_path: Path, output_path: Path, chunk_size: int) -> int:
    raw_text = transcript_path.read_text(encoding="utf-8")
    cleaned = strip_boilerplate(raw_text)
    mode = choose_mode(cleaned)
    chunks = split_into_chunks(cleaned, mode=mode, chunk_size=chunk_size)

    payload = {
        "episode_id": transcript_path.stem,
        "source_file": transcript_path.name,
        "chunk_mode": mode,
        "chunk_size": chunk_size if mode == "fixed" else None,
        "chunk_count": len(chunks),
        "chunks": [{"index": c.index, "text": c.text} for c in chunks],
    }
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return len(chunks)


def parse_args() -> argparse.Namespace:
    data_dir = get_data_dir(must_exist=False)
    transcripts_dir = data_dir / "transcripts"
    out_dir = data_dir / "episode_timeline_chunks"

    parser = argparse.ArgumentParser(
        description="Build chunked episode timeline files from transcripts.",
    )
    parser.add_argument(
        "--run-root",
        type=Path,
        default=None,
        help="Optional numbered run root. Uses 01-transcripts and 02-chunks under this root.",
    )
    parser.add_argument(
        "--transcripts-dir",
        type=Path,
        default=None,
        help=f"Directory with transcript .txt files (default: {transcripts_dir})",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help=f"Output directory for chunked timeline files (default: {out_dir})",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=DEFAULT_CHUNK_SIZE,
        help=f"Fixed chunk size for continuous text (default: {DEFAULT_CHUNK_SIZE})",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    default_data_dir = get_data_dir(must_exist=False)
    transcripts_dir = (
        args.transcripts_dir
        or (run_stage_path(args.run_root, "transcripts") if args.run_root else None)
        or (default_data_dir / "transcripts")
    )
    output_dir = (
        args.output_dir
        or (run_stage_path(args.run_root, "chunks") if args.run_root else None)
        or (default_data_dir / "episode_timeline_chunks")
    )
    chunk_size: int = args.chunk_size

    if not transcripts_dir.exists():
        if args.run_root and args.transcripts_dir is None:
            raise FileNotFoundError(
                f"Transcripts directory not found: {transcripts_dir}\n"
                "Expected numbered input folder 01-transcripts under the run root."
            )
        raise FileNotFoundError(f"Transcripts directory not found: {transcripts_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)
    transcript_files = sorted(transcripts_dir.glob("*.txt"))
    if not transcript_files:
        raise FileNotFoundError(f"No transcript files found in: {transcripts_dir}")

    total_chunks = 0
    for transcript_path in transcript_files:
        output_name = f"{transcript_path.stem}.chunks.json"
        output_path = output_dir / output_name
        chunk_count = build_one(transcript_path, output_path, chunk_size=chunk_size)
        total_chunks += chunk_count

    print(f"Processed {len(transcript_files)} transcripts")
    print(f"Wrote output to: {output_dir}")
    print(f"Total chunks: {total_chunks}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
