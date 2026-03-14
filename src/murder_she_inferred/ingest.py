"""Transcript ingestion (FR-1).

Loads plain-text transcripts from local files, preserves original order,
and splits them into sequential chunks for downstream analysis.

Supports two transcript formats:
- Screenplay format with INT./EXT. slug lines (split by scene)
- Continuous-text transcripts requiring boilerplate stripping and
  fixed-size chunking
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from murder_she_inferred.models import Chunk, EpisodeMetadata, EpisodeTimeline

# ---------------------------------------------------------------------------
# Slug-line detection for screenplay-format transcripts
# ---------------------------------------------------------------------------
_SLUG_LINE_RE = re.compile(
    r"^\s*(?:INT\.|EXT\.|INT\./EXT\.|EXT\./INT\.|INT/EXT|I/E\.)\s",
    re.IGNORECASE | re.MULTILINE,
)

# ---------------------------------------------------------------------------
# Boilerplate patterns for web-sourced transcripts
# ---------------------------------------------------------------------------
# Header: everything up to and including the "Posted: ... by ..." line
_BOILERPLATE_HEADER_RE = re.compile(
    r"^.*?Posted:\s*\d{2}/\d{2}/\d{2}\s+\d{2}:\d{2}\s+by\s+\S+\s*",
    re.DOTALL,
)

# Footer: common site-generated lines at the end
_BOILERPLATE_FOOTER_RE = re.compile(
    r"\s*All times are UTC[^\n]*$"
    r"|\s*Page \d+ of \d+\s*$"
    r"|\s*Powered by [^\n]*Forum Software[^\n]*$",
    re.MULTILINE,
)

# Default target chunk size in characters for fixed-mode splitting.
DEFAULT_CHUNK_SIZE = 2000


def load_transcript(path: str | Path) -> str:
    """Read a transcript file and return its full text."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Transcript not found: {path}")
    return path.read_text(encoding="utf-8")


def strip_boilerplate(text: str) -> str:
    """Remove surrounding boilerplate (header/footer) from a transcript.

    Handles transcripts that carry site-generated metadata and footer
    content. If the text doesn't match any known boilerplate pattern it
    is returned unchanged.
    """
    # Strip header (everything up to and including "Posted: ... by ...")
    text = _BOILERPLATE_HEADER_RE.sub("", text, count=1)
    # Strip footer lines
    text = _BOILERPLATE_FOOTER_RE.sub("", text)
    return text.strip()


def split_into_chunks(
    text: str,
    mode: str = "scene",
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> list[Chunk]:
    """Split transcript text into sequential chunks.

    Args:
        text: Full transcript text.
        mode: Splitting strategy.
            - "scene": Split on screenplay slug lines (INT./EXT.).
              Falls back to paragraph splitting if no slug lines found.
            - "paragraph": Split on blank-line-separated blocks.
            - "line": Each non-empty line becomes a chunk.
            - "fixed": Fixed-size chunks that break at sentence boundaries.
              Suited for continuous-text transcripts without scene markers.
        chunk_size: Target chunk size in characters (only used by "fixed"
            mode). Defaults to 2000.

    Returns:
        Ordered list of Chunk objects.
    """
    if mode == "line":
        segments = [line.strip() for line in text.splitlines() if line.strip()]
    elif mode == "paragraph":
        segments = _split_paragraphs(text)
    elif mode == "scene":
        segments = _split_scenes(text)
    elif mode == "fixed":
        segments = _split_fixed(text, chunk_size)
    else:
        raise ValueError(
            f"Unknown chunk mode: {mode!r}. "
            "Use 'scene', 'paragraph', 'line', or 'fixed'."
        )

    return [Chunk(index=i, text=seg) for i, seg in enumerate(segments)]


# ---------------------------------------------------------------------------
# Splitting strategies
# ---------------------------------------------------------------------------

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


def _split_fixed(text: str, target_size: int) -> list[str]:
    """Split continuous text into roughly equal-sized chunks.

    Breaks at sentence-ending punctuation (. ! ?) near the target size so
    chunks don't cut mid-sentence. If no sentence boundary is found within
    a reasonable window, falls back to the nearest space.

    This is the primary strategy for continuous-text transcripts that lack
    slug lines or reliable paragraph breaks.
    """
    text = text.strip()
    if not text:
        return []

    if len(text) <= target_size:
        return [text]

    chunks: list[str] = []
    start = 0

    while start < len(text):
        # If remaining text fits in one chunk, take it all.
        if start + target_size >= len(text):
            chunk = text[start:].strip()
            if chunk:
                chunks.append(chunk)
            break

        # Look for a sentence boundary near the target size.
        # Search in a window: [target * 0.7, target * 1.3]
        window_lo = start + int(target_size * 0.7)
        window_hi = min(start + int(target_size * 1.3), len(text))
        candidate = text[start:window_hi]

        # Find the last sentence-ending punctuation in the window.
        best = -1
        for m in re.finditer(r'[.!?][\s"\')]', candidate):
            pos = m.start() + 1  # include the punctuation itself
            if pos >= int(target_size * 0.7):
                best = pos

        if best > 0:
            split_at = start + best
        else:
            # No sentence boundary — fall back to last space before target.
            space_pos = text.rfind(" ", start, start + target_size)
            split_at = space_pos if space_pos > start else start + target_size

        chunk = text[start:split_at].strip()
        if chunk:
            chunks.append(chunk)
        start = split_at

        # Skip any leading whitespace for the next chunk.
        while start < len(text) and text[start] in " \t\n\r":
            start += 1

    return chunks


def _is_trivial_preamble(text: str) -> bool:
    """Check if preamble text is just boilerplate (FADE IN, etc.)."""
    stripped = re.sub(r"[:\s]", "", text).upper()
    return stripped in ("FADEIN", "FADEIN:", "")


# ---------------------------------------------------------------------------
# High-level ingestion pipeline
# ---------------------------------------------------------------------------

def ingest_episode(
    transcript_path: str | Path,
    metadata: Optional[EpisodeMetadata] = None,
    chunk_mode: str = "scene",
    *,
    strip_boilerplate_text: bool = False,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> EpisodeTimeline:
    """Full ingestion pipeline: load transcript and produce an EpisodeTimeline.

    Args:
        transcript_path: Path to the plain-text transcript file.
        metadata: Episode metadata. If None, a placeholder is created from
            the filename.
        chunk_mode: How to split the transcript ('scene', 'paragraph',
            'line', or 'fixed').
        strip_boilerplate_text: If True, remove site-generated header and
            footer content before splitting.
        chunk_size: Target chunk size in characters for 'fixed' mode.

    Returns:
        An EpisodeTimeline with chunks populated and ready for analysis.
    """
    transcript_path = Path(transcript_path)
    text = load_transcript(transcript_path)

    if strip_boilerplate_text:
        text = strip_boilerplate(text)

    chunks = split_into_chunks(text, mode=chunk_mode, chunk_size=chunk_size)

    if metadata is None:
        metadata = EpisodeMetadata(title=transcript_path.stem)

    return EpisodeTimeline(metadata=metadata, chunks=chunks)
