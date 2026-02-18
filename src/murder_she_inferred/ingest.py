"""Transcript ingestion (FR-1).

Loads plain-text transcripts from local files, preserves original order,
and splits them into sequential chunks for downstream analysis.

Scene splitting recognizes standard screenplay slug lines (INT./EXT.) as
scene boundaries, grouping all dialogue and action between two slug lines
into a single chunk.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from murder_she_inferred.models import Chunk, EpisodeMetadata, EpisodeTimeline

# Matches screenplay slug lines: INT. or EXT. at the start of a line,
# optionally preceded by whitespace. Covers common variants like
# "INT./EXT.", "INT/EXT", "I/E.".
_SLUG_LINE_RE = re.compile(
    r"^\s*(?:INT\.|EXT\.|INT\./EXT\.|EXT\./INT\.|INT/EXT|I/E\.)\s",
    re.IGNORECASE | re.MULTILINE,
)


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
            - "scene": Split on screenplay slug lines (INT./EXT.).
              Each chunk contains the slug line and everything up to the
              next slug line. Any text before the first slug line (e.g.
              FADE IN:) is included as chunk 0 if non-trivial.
            - "paragraph": Split on blank-line-separated blocks.
            - "line": Each non-empty line becomes a chunk.

    Returns:
        Ordered list of Chunk objects.
    """
    if mode == "line":
        segments = [line.strip() for line in text.splitlines() if line.strip()]
    elif mode == "paragraph":
        segments = _split_paragraphs(text)
    elif mode == "scene":
        segments = _split_scenes(text)
    else:
        raise ValueError(
            f"Unknown chunk mode: {mode!r}. Use 'scene', 'paragraph', or 'line'."
        )

    return [Chunk(index=i, text=seg) for i, seg in enumerate(segments)]


def _split_paragraphs(text: str) -> list[str]:
    """Split text into blocks separated by one or more blank lines."""
    blocks = re.split(r"\n\s*\n", text)
    return [block.strip() for block in blocks if block.strip()]


def _split_scenes(text: str) -> list[str]:
    """Split a screenplay-format transcript into scenes using slug lines.

    Each scene starts with a slug line (INT./EXT.) and includes all text
    up to the next slug line. Any preamble before the first slug line
    (e.g. "FADE IN:", title cards) is included as the first chunk if it
    contains meaningful content (more than just whitespace or "FADE IN").
    """
    matches = list(_SLUG_LINE_RE.finditer(text))

    if not matches:
        # No slug lines found — fall back to paragraph splitting so the
        # caller still gets usable chunks.
        return _split_paragraphs(text)

    scenes: list[str] = []

    # Handle any preamble before the first slug line.
    preamble = text[: matches[0].start()].strip()
    if preamble and not _is_trivial_preamble(preamble):
        scenes.append(preamble)

    # Each scene runs from one slug line to the next.
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        scene_text = text[start:end].strip()
        if scene_text:
            scenes.append(scene_text)

    return scenes


def _is_trivial_preamble(text: str) -> bool:
    """Check if preamble text is just boilerplate (FADE IN, etc.)."""
    stripped = re.sub(r"[:\s]", "", text).upper()
    return stripped in ("FADEIN", "FADEIN:", "")


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
