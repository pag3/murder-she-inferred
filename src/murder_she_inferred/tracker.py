"""Suspect state tracking (FR-3) and evidence annotation (FR-4).

Maintains the running set of suspects and their states across chunks,
and attaches lightweight evidence notes at chunk boundaries.
"""

from __future__ import annotations

from murder_she_inferred.models import (
    EpisodeTimeline,
    EvidenceNote,
    EvidenceType,
    SuspectRecord,
    SuspectState,
)


class SuspectTracker:
    """Incrementally tracks suspect states for an episode timeline.

    Wraps an EpisodeTimeline and provides methods to introduce suspects,
    eliminate them, and attach evidence notes — all indexed by chunk.
    """

    def __init__(self, timeline: EpisodeTimeline) -> None:
        self.timeline = timeline

    def introduce_suspect(self, name: str, chunk_index: int) -> SuspectRecord:
        """Add a new suspect at the given chunk index.

        If the suspect already exists, returns the existing record unchanged.
        """
        if name in self.timeline.suspects:
            return self.timeline.suspects[name]

        record = SuspectRecord(name=name, introduced_at=chunk_index)
        self.timeline.suspects[name] = record
        return record

    def eliminate_suspect(self, name: str, chunk_index: int) -> SuspectRecord:
        """Mark a suspect as eliminated at the given chunk index.

        Raises KeyError if the suspect hasn't been introduced.
        """
        if name not in self.timeline.suspects:
            raise KeyError(f"Unknown suspect: {name!r}")

        record = self.timeline.suspects[name]
        if record.state == SuspectState.ELIMINATED:
            return record  # already eliminated, no-op

        record.eliminate(chunk_index)
        return record

    def add_evidence(
        self,
        chunk_index: int,
        evidence_type: EvidenceType,
        character: str,
        note: str = "",
    ) -> EvidenceNote:
        """Attach an evidence annotation at a chunk boundary (FR-4)."""
        evidence = EvidenceNote(
            chunk_index=chunk_index,
            evidence_type=evidence_type,
            character=character,
            note=note,
        )
        self.timeline.evidence.append(evidence)
        return evidence

    def implicate(
        self, character: str, chunk_index: int, note: str = ""
    ) -> EvidenceNote:
        """Shorthand: add implicating evidence for a character."""
        return self.add_evidence(chunk_index, EvidenceType.IMPLICATES, character, note)

    def clear(self, character: str, chunk_index: int, note: str = "") -> EvidenceNote:
        """Shorthand: add clearing evidence for a character."""
        return self.add_evidence(chunk_index, EvidenceType.CLEARS, character, note)

    @property
    def active_suspects(self) -> list[SuspectRecord]:
        """Return currently active suspects."""
        return self.timeline.active_suspects()

    @property
    def eliminated_suspects(self) -> list[SuspectRecord]:
        """Return eliminated suspects."""
        return self.timeline.eliminated_suspects()

    def get_state_at(self, chunk_index: int) -> dict[str, SuspectState]:
        """Get suspect states as of a particular chunk."""
        return self.timeline.suspects_at_chunk(chunk_index)

    def evidence_for_chunk(self, chunk_index: int) -> list[EvidenceNote]:
        """Return all evidence notes attached to a specific chunk."""
        return [e for e in self.timeline.evidence if e.chunk_index == chunk_index]

    def summary(self) -> str:
        """Return a human-readable summary of the current state."""
        lines = [f"Episode: {self.timeline.metadata.title}"]
        lines.append(f"Chunks processed: {len(self.timeline.chunks)}")
        lines.append(f"Active suspects: {len(self.active_suspects)}")
        for s in self.active_suspects:
            lines.append(f"  - {s.name} (since chunk {s.introduced_at})")
        lines.append(f"Eliminated suspects: {len(self.eliminated_suspects)}")
        for s in self.eliminated_suspects:
            lines.append(
                f"  - {s.name} (chunks {s.introduced_at}–{s.eliminated_at})"
            )
        if self.timeline.evidence:
            lines.append(f"Evidence notes: {len(self.timeline.evidence)}")
            for e in self.timeline.evidence:
                lines.append(f"  {e}")
        return "\n".join(lines)
