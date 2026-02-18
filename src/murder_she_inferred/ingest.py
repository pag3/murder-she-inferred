"""Transcript ingestion (FR-1).

Loads plain-text transcripts from local files, preserves original order,
and splits them into sequential chunks for downstream analysis.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from murder_she_inferred.models import Chunk, EpisodeMetadata, EpisodeTimeline


def load_transcript(path: str | Path) -> str:
    """Read a transcript file and return its full text."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Transcript not found: {path}")
    return path.read_text(encoding="utf-8")


def split_into_chunks(text: str, mode: str = "scene") -> list[Chunk]:
    """Split transcript text into sequential chunks.

    Args:
        text: Full transcript text.
        mode: Splitting strategy.
            - "scene": Split on blank-line-separated blocks (default).
            - "line": Each non-empty line becomes a chunk.

    Returns:
        Ordered list of Chunk objects.
    """
    if mode == "line":
        segments = [line.strip() for line in text.splitlines() if line.strip()]
    elif mode == "scene":
        segments = _split_scenes(text)
    else:
        raise ValueError(f"Unknown chunk mode: {mode!r}. Use 'scene' or 'line'.")

    return [Chunk(index=i, text=seg) for i, seg in enumerate(segments)]


def _split_scenes(text: str) -> list[str]:
    """Split text into scene-like blocks separated by one or more blank lines."""
    blocks = re.split(r"\n\s*\n", text)
    return [block.strip() for block in blocks if block.strip()]


def ingest_episode(
    transcript_path: str | Path,
    metadata: Optional[EpisodeMetadata] = None,
    chunk_mode: str = "scene",
) -> EpisodeTimeline:
    """Full ingestion pipeline: load transcript and produce an EpisodeTimeline.

    Args:
        transcript_path: Path to the plain-text transcript file.
        metadata: Episode metadata. If None, a placeholder is created from
            the filename.
        chunk_mode: How to split the transcript ('scene' or 'line').

    Returns:
        An EpisodeTimeline with chunks populated and ready for analysis.
    """
    transcript_path = Path(transcript_path)
    text = load_transcript(transcript_path)
    chunks = split_into_chunks(text, mode=chunk_mode)

    if metadata is None:
        metadata = EpisodeMetadata(title=transcript_path.stem)

    return EpisodeTimeline(metadata=metadata, chunks=chunks)
