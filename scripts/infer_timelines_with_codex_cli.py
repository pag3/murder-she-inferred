#!/usr/bin/env python3
"""Infer suspect timelines from chunk files using Codex CLI."""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import time
from pathlib import Path
from typing import Any

from murder_she_inferred.models import Chunk, EpisodeMetadata, EpisodeTimeline, SuspectState
from murder_she_inferred.settings import get_data_dir, run_stage_path
from murder_she_inferred.tracker import SuspectTracker

SYSTEM_PROMPT = """You are extracting suspect timeline updates from a mystery transcript.
Return strict JSON only. No markdown. No explanations.
Schema:
{
  "introduced": ["name", ...],
  "eliminated": ["name", ...],
  "evidence": [
    {"type":"implicates|clears","character":"name","note":"short note"}
  ]
}
Rules:
- Use only the provided cumulative transcript context and prior state.
- Keep names consistent and concise.
- Do not hallucinate facts not present in the transcript so far.
- If the chunk strongly clears a suspect (alibi, impossibility, confession by another), include them in "eliminated".
- If the chunk contains a reveal/confession/explicit killer identification, aggressively eliminate alternatives that are no longer plausible.
- Public accusations/arrests are weak evidence by default unless corroborated by concrete clues.
- If nothing changes, return empty lists.
"""


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


def _extract_json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    if not text:
        raise ValueError("Empty response from Codex CLI")

    if text.startswith("```"):
        parts = text.split("```")
        for part in parts:
            candidate = part.strip()
            if candidate.startswith("json"):
                candidate = candidate[4:].strip()
            if candidate.startswith("{") and candidate.endswith("}"):
                return json.loads(candidate)

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Could not find JSON object in Codex CLI output")
    return json.loads(text[start : end + 1])


def _normalize_result(payload: dict[str, Any]) -> dict[str, Any]:
    introduced = payload.get("introduced", [])
    eliminated = payload.get("eliminated", [])
    evidence = payload.get("evidence", [])

    if not isinstance(introduced, list):
        introduced = []
    if not isinstance(eliminated, list):
        eliminated = []
    if not isinstance(evidence, list):
        evidence = []

    clean_evidence: list[dict[str, str]] = []
    for item in evidence:
        if not isinstance(item, dict):
            continue
        ev_type = str(item.get("type", "")).strip().lower()
        if ev_type not in {"implicates", "clears"}:
            continue
        character = str(item.get("character", "")).strip()
        if not character:
            continue
        note = str(item.get("note", "")).strip()
        clean_evidence.append({"type": ev_type, "character": character, "note": note})

    return {
        "introduced": [str(x).strip() for x in introduced if str(x).strip()],
        "eliminated": [str(x).strip() for x in eliminated if str(x).strip()],
        "evidence": clean_evidence,
    }


def _build_prompt(
    *,
    episode_id: str,
    chunk_index: int,
    cumulative_text: str,
    current_chunk_text: str,
    active_suspects: list[str],
    eliminated_suspects: list[str],
) -> str:
    state = {
        "episode_id": episode_id,
        "chunk_index": chunk_index,
        "active_suspects": active_suspects,
        "eliminated_suspects": eliminated_suspects,
    }
    return (
        f"{SYSTEM_PROMPT}\n\n"
        f"Prior state:\n{json.dumps(state, ensure_ascii=False, indent=2)}\n\n"
        "Transcript so far (chunks 0..current):\n"
        f"{cumulative_text}\n\n"
        "Current chunk text:\n"
        f"{current_chunk_text}\n"
    )


def _call_codex(command: str, prompt: str) -> str:
    command = _normalize_codex_command(command)
    completed = subprocess.run(
        command,
        shell=True,
        input=prompt,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"Codex command failed ({completed.returncode}): {completed.stderr.strip()}"
        )
    return completed.stdout


def _normalize_codex_command(command: str) -> str:
    """Ensure Codex command runs in non-interactive mode."""
    parts = shlex.split(command)
    if not parts:
        raise ValueError("codex command is empty")
    binary = Path(parts[0]).name
    if binary == "codex" and len(parts) == 1:
        return f"{command} exec -"
    return command


def _build_timeline(chunks_payload: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    episode_id = str(chunks_payload.get("episode_id", "unknown-episode"))
    chunk_objs = chunks_payload.get("chunks", [])
    if not isinstance(chunk_objs, list):
        raise ValueError("Invalid chunks payload: 'chunks' must be a list")

    chunks = [
        Chunk(index=int(c["index"]), text=str(c["text"]))
        for c in chunk_objs
        if isinstance(c, dict) and "index" in c and "text" in c
    ]
    if args.max_chunks is not None:
        chunks = chunks[: args.max_chunks]

    timeline = EpisodeTimeline(metadata=EpisodeMetadata(title=episode_id), chunks=chunks)
    tracker = SuspectTracker(timeline)

    chunk_events: list[dict[str, Any]] = []
    cumulative_parts: list[str] = []
    for chunk in chunks:
        cumulative_parts.append(f"[Chunk {chunk.index}]\n{chunk.text}")
        cumulative_text = "\n\n".join(cumulative_parts)
        active_now = sorted(s.name for s in tracker.active_suspects)
        eliminated_now = sorted(s.name for s in tracker.eliminated_suspects)
        prompt = _build_prompt(
            episode_id=episode_id,
            chunk_index=chunk.index,
            cumulative_text=cumulative_text,
            current_chunk_text=chunk.text,
            active_suspects=active_now,
            eliminated_suspects=eliminated_now,
        )

        result: dict[str, Any] | None = None
        last_error = ""
        for _attempt in range(args.retries + 1):
            try:
                raw = _call_codex(args.codex_command, prompt)
                result = _normalize_result(_extract_json_object(raw))
                break
            except Exception as exc:  # pragma: no cover - CLI failure path
                last_error = str(exc)
                result = None

        if result is None:
            result = {"introduced": [], "eliminated": [], "evidence": []}

        for name in result["introduced"]:
            tracker.introduce_suspect(name, chunk.index)

        for name in result["eliminated"]:
            if name not in tracker.timeline.suspects:
                tracker.introduce_suspect(name, chunk.index)
            tracker.eliminate_suspect(name, chunk.index)

        for ev in result["evidence"]:
            if ev["type"] == "implicates":
                tracker.implicate(ev["character"], chunk.index, note=ev["note"])
            else:
                tracker.clear(ev["character"], chunk.index, note=ev["note"])

        state_after = tracker.get_state_at(chunk.index)
        chunk_events.append(
            {
                "chunk_index": chunk.index,
                "introduced": result["introduced"],
                "eliminated": result["eliminated"],
                "evidence": result["evidence"],
                "active_suspects_after_chunk": sorted(
                    [name for name, st in state_after.items() if st == SuspectState.ACTIVE]
                ),
                "eliminated_suspects_after_chunk": sorted(
                    [name for name, st in state_after.items() if st == SuspectState.ELIMINATED]
                ),
                "error": last_error if last_error and not any(result.values()) else "",
            }
        )
        if args.sleep_seconds > 0:
            time.sleep(args.sleep_seconds)

    final_state = tracker.get_state_at(chunks[-1].index) if chunks else {}
    return {
        "episode_id": episode_id,
        "source_file": chunks_payload.get("source_file"),
        "chunk_mode": chunks_payload.get("chunk_mode"),
        "chunk_count": len(chunks),
        "events": chunk_events,
        "final_active_suspects": sorted(
            [name for name, st in final_state.items() if st == SuspectState.ACTIVE]
        ),
        "final_eliminated_suspects": sorted(
            [name for name, st in final_state.items() if st == SuspectState.ELIMINATED]
        ),
        "total_evidence_notes": len(tracker.timeline.evidence),
    }


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
    for path in files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        timeline_payload = _build_timeline(payload, args)
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
