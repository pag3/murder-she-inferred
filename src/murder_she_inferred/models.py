"""Core data models for Murder, She Inferred."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class SuspectState(Enum):
    """Possible states for a suspect during an episode."""

    ACTIVE = "active"
    ELIMINATED = "eliminated"


class EvidenceType(Enum):
    """Type of evidence annotation."""

    IMPLICATES = "implicates"
    CLEARS = "clears"


@dataclass
class EpisodeMetadata:
    """Metadata for a Murder, She Wrote episode."""

    title: str
    season: Optional[int] = None
    episode: Optional[int] = None
    year: Optional[int] = None


@dataclass
class Chunk:
    """A sequential unit of transcript text (line, beat, or scene)."""

    index: int
    text: str


@dataclass
class EvidenceNote:
    """A lightweight evidence annotation attached to a chunk boundary (FR-4)."""

    chunk_index: int
    evidence_type: EvidenceType
    character: str
    note: str = ""

    def __str__(self) -> str:
        verb = "implicates" if self.evidence_type == EvidenceType.IMPLICATES else "clears"
        base = f"[Chunk {self.chunk_index}] {verb} {self.character}"
        if self.note:
            base += f" — {self.note}"
        return base


@dataclass
class SuspectRecord:
    """Tracks a single suspect's state across the episode timeline."""

    name: str
    introduced_at: int  # chunk index where first identified as suspect
    state: SuspectState = SuspectState.ACTIVE
    eliminated_at: Optional[int] = None  # chunk index where eliminated
    transitions: list[tuple[int, SuspectState]] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Seed state history with the initial introduction."""
        if not self.transitions:
            self.transitions.append((self.introduced_at, SuspectState.ACTIVE))

    def eliminate(self, chunk_index: int) -> None:
        """Mark this suspect as eliminated at the given chunk."""
        if self.state == SuspectState.ELIMINATED:
            return
        self.state = SuspectState.ELIMINATED
        self.eliminated_at = chunk_index
        self.transitions.append((chunk_index, SuspectState.ELIMINATED))

    def reactivate(self, chunk_index: int) -> None:
        """Mark this suspect as active again at the given chunk."""
        if self.state == SuspectState.ACTIVE:
            return
        self.state = SuspectState.ACTIVE
        self.eliminated_at = None
        self.transitions.append((chunk_index, SuspectState.ACTIVE))


@dataclass
class EpisodeTimeline:
    """Complete timeline of an episode's suspect tracking (FR-3 output).

    This is the central data structure: it holds chunks, suspects, and
    evidence notes for a single episode analysis.
    """

    metadata: EpisodeMetadata
    chunks: list[Chunk] = field(default_factory=list)
    suspects: dict[str, SuspectRecord] = field(default_factory=dict)
    evidence: list[EvidenceNote] = field(default_factory=list)

    def active_suspects(self) -> list[SuspectRecord]:
        """Return all currently active suspects."""
        return [s for s in self.suspects.values() if s.state == SuspectState.ACTIVE]

    def eliminated_suspects(self) -> list[SuspectRecord]:
        """Return all eliminated suspects."""
        return [s for s in self.suspects.values() if s.state == SuspectState.ELIMINATED]

    def suspects_at_chunk(self, chunk_index: int) -> dict[str, SuspectState]:
        """Return the suspect states as of a given chunk index.

        Reconstructs the state by replaying suspect transitions up to and
        including the specified chunk.
        """
        states: dict[str, SuspectState] = {}
        for suspect in self.suspects.values():
            if suspect.introduced_at > chunk_index:
                continue
            current_state = SuspectState.ACTIVE
            for transition_chunk, transition_state in suspect.transitions:
                if transition_chunk > chunk_index:
                    break
                current_state = transition_state
            states[suspect.name] = current_state
        return states
