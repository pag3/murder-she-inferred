#!/usr/bin/env python3
"""Quality checks for generated timeline JSON files."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run QC checks across *.timeline.json files.",
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        required=True,
        help="Directory containing timeline JSON files.",
    )
    parser.add_argument(
        "--max-error-rate",
        type=float,
        default=0.2,
        help="Flag episodes above this per-chunk error rate (default: 0.2).",
    )
    parser.add_argument(
        "--report-path",
        type=Path,
        default=None,
        help="Optional path to write QC report JSON.",
    )
    return parser.parse_args()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _contains_error(event: dict[str, Any]) -> bool:
    return bool(str(event.get("error", "")).strip())


def _is_empty_event(event: dict[str, Any]) -> bool:
    introduced = event.get("introduced") or []
    eliminated = event.get("eliminated") or []
    evidence = event.get("evidence") or []
    return not introduced and not eliminated and not evidence


def _state_set(event: dict[str, Any], key: str) -> set[str]:
    val = event.get(key) or []
    return {str(x).strip() for x in val if str(x).strip()}


def qc_file(path: Path, max_error_rate: float) -> dict[str, Any]:
    payload = _read_json(path)
    events = payload.get("events") or []
    chunk_count = int(payload.get("chunk_count", len(events)))

    errors = [e for e in events if isinstance(e, dict) and _contains_error(e)]
    empty_events = [e for e in events if isinstance(e, dict) and _is_empty_event(e)]
    error_rate = (len(errors) / chunk_count) if chunk_count else 0.0
    empty_rate = (len(empty_events) / chunk_count) if chunk_count else 0.0

    issues: list[str] = []
    if chunk_count == 0:
        issues.append("no_chunks")
    if len(empty_events) == chunk_count and chunk_count > 0:
        issues.append("all_events_empty")
    if error_rate > max_error_rate:
        issues.append("high_error_rate")

    repeated_error = ""
    if errors:
        top = Counter(str(e.get("error", "")).strip() for e in errors).most_common(1)
        repeated_error = top[0][0]
        if len(top) == 1 and len(errors) == chunk_count:
            issues.append("all_chunks_error")

    # Consistency check: a name cannot appear active and eliminated simultaneously.
    inconsistent_chunks: list[int] = []
    for event in events:
        if not isinstance(event, dict):
            continue
        idx = int(event.get("chunk_index", -1))
        active = _state_set(event, "active_suspects_after_chunk")
        eliminated = _state_set(event, "eliminated_suspects_after_chunk")
        if active.intersection(eliminated):
            inconsistent_chunks.append(idx)
    if inconsistent_chunks:
        issues.append("inconsistent_state_overlap")

    return {
        "file": path.name,
        "episode_id": payload.get("episode_id", path.stem),
        "chunk_count": chunk_count,
        "error_chunks": len(errors),
        "error_rate": round(error_rate, 4),
        "empty_chunks": len(empty_events),
        "empty_rate": round(empty_rate, 4),
        "repeated_error": repeated_error,
        "issues": issues,
        "inconsistent_chunks": inconsistent_chunks,
    }


def main() -> int:
    args = parse_args()
    input_dir: Path = args.input_dir
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    files = sorted(input_dir.glob("*.timeline.json"))
    if not files:
        raise FileNotFoundError(f"No timeline files found in: {input_dir}")

    results = [qc_file(path, args.max_error_rate) for path in files]
    flagged = [r for r in results if r["issues"]]

    summary = {
        "input_dir": str(input_dir),
        "file_count": len(results),
        "flagged_count": len(flagged),
        "max_error_rate": args.max_error_rate,
        "flagged_files": flagged,
    }

    print(f"QC scanned files: {len(results)}")
    print(f"Flagged files: {len(flagged)}")
    if flagged:
        print("Top flagged episodes:")
        for row in flagged[:20]:
            issue_str = ",".join(row["issues"])
            print(
                f"- {row['file']} | issues={issue_str} "
                f"| error_rate={row['error_rate']:.2f} "
                f"| empty_rate={row['empty_rate']:.2f}"
            )

    if args.report_path:
        args.report_path.parent.mkdir(parents=True, exist_ok=True)
        args.report_path.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"Wrote report: {args.report_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
