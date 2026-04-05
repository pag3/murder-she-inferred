"""Reusable inference logic: prompt building, JSON extraction, and timeline construction."""

from __future__ import annotations

import json
import time
from typing import Any, Callable

from murder_she_inferred.models import Chunk, EpisodeMetadata, EpisodeTimeline, SuspectState
from murder_she_inferred.tracker import SuspectTracker

SYSTEM_PROMPT = """You are extracting suspect timeline updates from a mystery transcript.
Return strict JSON only. No markdown. No explanations.
Schema:
{
  "introduced": ["name", ...],
  "eliminated": ["name", ...],
  "evidence": [
    {"type":"implicates|clears","character":"name","note":"short note"}
  ],
  "suspicion_scores": {"name": 0-100, ...}
}
Rules:
- Use only the provided cumulative transcript context and prior state.
- Keep names consistent and prefer full names over shorthand.
- Reuse the most specific full name already established in the transcript or prior state; avoid switching between aliases, titles, first names, and surnames for the same person.
- Do not hallucinate facts not present in the transcript so far.
- If the chunk strongly clears a suspect (alibi, impossibility, confession by another), include them in "eliminated".
- If the chunk contains a reveal/confession/explicit killer identification, aggressively eliminate alternatives that are no longer plausible.
- If a previously eliminated suspect becomes plausible again, include them in "introduced" so they become active again.
- Track the principal wrongdoer(s) for the episode's central mystery. If the chunk distinguishes the actual killer from an accomplice, coerced helper, cover-up participant, self-defender, victim, or suicide, keep that distinction clear in both state updates and evidence notes.
- Do not leave a self-defender, accident victim, or suicide victim active as the murderer once the transcript clarifies what really happened.
- When two different crimes are disentangled late in the episode, keep active only the people still plausibly responsible for intentional wrongdoing that Jessica is exposing in the current reveal.
- Public accusations/arrests are weak evidence by default unless corroborated by concrete clues.
- If nothing changes, return empty lists and keep suspicion_scores the same as before.

Suspicion scores:
- "suspicion_scores" maps each currently active suspect name to an integer 0-100.
- Scores represent relative suspicion and should sum to approximately 100.
- Higher score = more suspicious based on all evidence so far.
- Eliminated suspects should not appear in suspicion_scores.
- Newly introduced suspects must be included in suspicion_scores.
- When a suspect is eliminated, redistribute their share among the remaining active suspects.
"""


def extract_json_object(text: str) -> dict[str, Any]:
    """Extract a JSON object from raw text, handling markdown fences."""
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


def normalize_result(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize and validate an inference result payload."""
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

    raw_scores = payload.get("suspicion_scores", {})
    clean_scores: dict[str, int] = {}
    if isinstance(raw_scores, dict):
        for name, score in raw_scores.items():
            name = str(name).strip()
            if not name:
                continue
            try:
                clean_scores[name] = max(0, min(100, int(score)))
            except (TypeError, ValueError):
                continue

    return {
        "introduced": [str(x).strip() for x in introduced if str(x).strip()],
        "eliminated": [str(x).strip() for x in eliminated if str(x).strip()],
        "evidence": clean_evidence,
        "suspicion_scores": clean_scores,
    }


def build_prompt(
    *,
    episode_id: str,
    chunk_index: int,
    context_text: str,
    current_chunk_text: str,
    active_suspects: list[str],
    eliminated_suspects: list[str],
    prior_scores: dict[str, int] | None = None,
) -> str:
    """Build a full inference prompt from prior state and transcript context."""
    state: dict[str, Any] = {
        "episode_id": episode_id,
        "chunk_index": chunk_index,
        "active_suspects": active_suspects,
        "eliminated_suspects": eliminated_suspects,
    }
    if prior_scores:
        state["prior_suspicion_scores"] = prior_scores
    return (
        f"{SYSTEM_PROMPT}\n\n"
        f"Prior state:\n{json.dumps(state, ensure_ascii=False, indent=2)}\n\n"
        "Recent transcript context:\n"
        f"{context_text}\n\n"
        "Current chunk text:\n"
        f"{current_chunk_text}\n"
    )


def build_timeline(
    chunks_payload: dict[str, Any],
    *,
    backend_fn: Callable[[str], str],
    max_chunks: int | None = None,
    context_window: int = 0,
    retries: int = 2,
    sleep_seconds: float = 0.0,
) -> dict[str, Any]:
    """Build a full episode timeline by calling backend_fn for each chunk."""
    episode_id = str(chunks_payload.get("episode_id", "unknown-episode"))
    chunk_objs = chunks_payload.get("chunks", [])
    if not isinstance(chunk_objs, list):
        raise ValueError("Invalid chunks payload: 'chunks' must be a list")

    chunks = [
        Chunk(index=int(c["index"]), text=str(c["text"]))
        for c in chunk_objs
        if isinstance(c, dict) and "index" in c and "text" in c
    ]
    if max_chunks is not None:
        chunks = chunks[:max_chunks]

    timeline = EpisodeTimeline(metadata=EpisodeMetadata(title=episode_id), chunks=chunks)
    tracker = SuspectTracker(timeline)

    chunk_events: list[dict[str, Any]] = []
    cumulative_parts: list[str] = []
    window_size = context_window
    prior_scores: dict[str, int] = {}
    total_chunks = len(chunks)
    for chunk in chunks:
        print(f"  chunk {chunk.index + 1}/{total_chunks}", flush=True)
        cumulative_parts.append(f"[Chunk {chunk.index}]\n{chunk.text}")
        if window_size > 0:
            window = cumulative_parts[-window_size:]
        else:
            window = cumulative_parts
        context_text = "\n\n".join(window)
        active_now = sorted(s.name for s in tracker.active_suspects)
        eliminated_now = sorted(s.name for s in tracker.eliminated_suspects)
        prompt = build_prompt(
            episode_id=episode_id,
            chunk_index=chunk.index,
            context_text=context_text,
            current_chunk_text=chunk.text,
            active_suspects=active_now,
            eliminated_suspects=eliminated_now,
            prior_scores=prior_scores if prior_scores else None,
        )

        result: dict[str, Any] | None = None
        last_error = ""
        for _attempt in range(retries + 1):
            try:
                raw = backend_fn(prompt)
                result = normalize_result(extract_json_object(raw))
                break
            except Exception as exc:
                last_error = str(exc)
                result = None

        if result is None:
            result = {"introduced": [], "eliminated": [], "evidence": [], "suspicion_scores": {}}

        for name in result["introduced"]:
            tracker.introduce_suspect(name, chunk.index)

        for name in result["eliminated"]:
            if name not in tracker.timeline.suspects:
                tracker.introduce_suspect(name, chunk.index)
            tracker.eliminate_suspect(name, chunk.index)

        for ev in result["evidence"]:
            if ev["type"] == "implicates":
                if (
                    ev["character"] in tracker.timeline.suspects
                    and ev["character"] not in result["eliminated"]
                ):
                    tracker.introduce_suspect(ev["character"], chunk.index)
                tracker.implicate(ev["character"], chunk.index, note=ev["note"])
            else:
                tracker.clear(ev["character"], chunk.index, note=ev["note"])

        prior_scores = result.get("suspicion_scores", {})

        state_after = tracker.get_state_at(chunk.index)
        chunk_events.append(
            {
                "chunk_index": chunk.index,
                "introduced": result["introduced"],
                "eliminated": result["eliminated"],
                "evidence": result["evidence"],
                "suspicion_scores": result.get("suspicion_scores", {}),
                "active_suspects_after_chunk": sorted(
                    [name for name, st in state_after.items() if st == SuspectState.ACTIVE]
                ),
                "eliminated_suspects_after_chunk": sorted(
                    [name for name, st in state_after.items() if st == SuspectState.ELIMINATED]
                ),
                "error": last_error if last_error and not any(result.values()) else "",
            }
        )
        if sleep_seconds > 0:
            time.sleep(sleep_seconds)

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
