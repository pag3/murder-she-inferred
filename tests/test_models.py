"""Tests for core data models."""

from murder_she_inferred.models import (
    Chunk,
    EpisodeMetadata,
    EpisodeTimeline,
    EvidenceNote,
    EvidenceType,
    SuspectRecord,
    SuspectState,
)


class TestSuspectState:
    def test_enum_values(self):
        assert SuspectState.ACTIVE.value == "active"
        assert SuspectState.ELIMINATED.value == "eliminated"


class TestEvidenceType:
    def test_enum_values(self):
        assert EvidenceType.IMPLICATES.value == "implicates"
        assert EvidenceType.CLEARS.value == "clears"


class TestSuspectRecord:
    def test_creation(self):
        suspect = SuspectRecord(name="Richard Cole", introduced_at=2)
        assert suspect.name == "Richard Cole"
        assert suspect.introduced_at == 2
        assert suspect.state == SuspectState.ACTIVE
        assert suspect.eliminated_at is None

    def test_eliminate(self):
        suspect = SuspectRecord(name="Frank Butler", introduced_at=3)
        suspect.eliminate(chunk_index=5)
        assert suspect.state == SuspectState.ELIMINATED
        assert suspect.eliminated_at == 5

    def test_reactivate(self):
        suspect = SuspectRecord(name="Frank Butler", introduced_at=3)
        suspect.eliminate(chunk_index=5)
        suspect.reactivate(chunk_index=7)
        assert suspect.state == SuspectState.ACTIVE
        assert suspect.eliminated_at is None
        assert suspect.transitions == [
            (3, SuspectState.ACTIVE),
            (5, SuspectState.ELIMINATED),
            (7, SuspectState.ACTIVE),
        ]


class TestEvidenceNote:
    def test_str_implicates(self):
        note = EvidenceNote(
            chunk_index=3,
            evidence_type=EvidenceType.IMPLICATES,
            character="Richard Cole",
            note="business dispute motive",
        )
        result = str(note)
        assert "implicates" in result
        assert "Richard Cole" in result
        assert "business dispute motive" in result

    def test_str_clears_no_note(self):
        note = EvidenceNote(
            chunk_index=5,
            evidence_type=EvidenceType.CLEARS,
            character="Frank Butler",
        )
        result = str(note)
        assert "clears" in result
        assert "Frank Butler" in result
        assert "—" not in result


class TestEpisodeTimeline:
    def _make_timeline(self):
        meta = EpisodeMetadata(title="Test Episode", season=1, episode=1)
        timeline = EpisodeTimeline(
            metadata=meta,
            chunks=[Chunk(index=i, text=f"chunk {i}") for i in range(5)],
        )
        timeline.suspects["Alice"] = SuspectRecord(name="Alice", introduced_at=1)
        timeline.suspects["Bob"] = SuspectRecord(name="Bob", introduced_at=2)
        timeline.suspects["Bob"].eliminate(chunk_index=4)
        return timeline

    def test_active_suspects(self):
        timeline = self._make_timeline()
        active = timeline.active_suspects()
        assert len(active) == 1
        assert active[0].name == "Alice"

    def test_eliminated_suspects(self):
        timeline = self._make_timeline()
        eliminated = timeline.eliminated_suspects()
        assert len(eliminated) == 1
        assert eliminated[0].name == "Bob"

    def test_suspects_at_chunk_before_introduction(self):
        timeline = self._make_timeline()
        states = timeline.suspects_at_chunk(0)
        assert len(states) == 0

    def test_suspects_at_chunk_mid_episode(self):
        timeline = self._make_timeline()
        states = timeline.suspects_at_chunk(3)
        assert states["Alice"] == SuspectState.ACTIVE
        assert states["Bob"] == SuspectState.ACTIVE

    def test_suspects_at_chunk_after_elimination(self):
        timeline = self._make_timeline()
        states = timeline.suspects_at_chunk(4)
        assert states["Alice"] == SuspectState.ACTIVE
        assert states["Bob"] == SuspectState.ELIMINATED

    def test_suspects_at_chunk_after_reactivation(self):
        timeline = self._make_timeline()
        timeline.suspects["Bob"].reactivate(chunk_index=5)

        assert timeline.suspects_at_chunk(4)["Bob"] == SuspectState.ELIMINATED
        assert timeline.suspects_at_chunk(5)["Bob"] == SuspectState.ACTIVE
