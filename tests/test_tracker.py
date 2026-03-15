"""Tests for suspect state tracking (FR-3) and evidence annotation (FR-4)."""

import pytest

from murder_she_inferred.models import (
    Chunk,
    EpisodeMetadata,
    EpisodeTimeline,
    EvidenceType,
    SuspectState,
)
from murder_she_inferred.tracker import SuspectTracker


@pytest.fixture
def tracker():
    """Create a tracker with a simple 6-chunk timeline."""
    meta = EpisodeMetadata(title="Test Episode", season=1, episode=1)
    timeline = EpisodeTimeline(
        metadata=meta,
        chunks=[Chunk(index=i, text=f"Scene {i}") for i in range(6)],
    )
    return SuspectTracker(timeline)


class TestSuspectIntroduction:
    def test_introduce_new_suspect(self, tracker):
        record = tracker.introduce_suspect("Richard Cole", chunk_index=1)
        assert record.name == "Richard Cole"
        assert record.introduced_at == 1
        assert record.state == SuspectState.ACTIVE

    def test_introduce_duplicate_returns_existing(self, tracker):
        first = tracker.introduce_suspect("Richard Cole", chunk_index=1)
        second = tracker.introduce_suspect("Richard Cole", chunk_index=3)
        assert first is second
        assert first.introduced_at == 1  # keeps original introduction

    def test_multiple_suspects(self, tracker):
        tracker.introduce_suspect("Alice", chunk_index=0)
        tracker.introduce_suspect("Bob", chunk_index=1)
        tracker.introduce_suspect("Charlie", chunk_index=2)
        assert len(tracker.active_suspects) == 3

    def test_reintroduce_eliminated_suspect_reactivates(self, tracker):
        tracker.introduce_suspect("Richard Cole", chunk_index=1)
        tracker.eliminate_suspect("Richard Cole", chunk_index=3)

        record = tracker.introduce_suspect("Richard Cole", chunk_index=5)

        assert record.state == SuspectState.ACTIVE
        assert record.introduced_at == 1
        assert record.eliminated_at is None


class TestSuspectElimination:
    def test_eliminate_suspect(self, tracker):
        tracker.introduce_suspect("Frank Butler", chunk_index=2)
        record = tracker.eliminate_suspect("Frank Butler", chunk_index=4)
        assert record.state == SuspectState.ELIMINATED
        assert record.eliminated_at == 4

    def test_eliminate_unknown_raises(self, tracker):
        with pytest.raises(KeyError, match="Unknown suspect"):
            tracker.eliminate_suspect("Nobody", chunk_index=3)

    def test_eliminate_already_eliminated_is_noop(self, tracker):
        tracker.introduce_suspect("Frank", chunk_index=1)
        tracker.eliminate_suspect("Frank", chunk_index=3)
        record = tracker.eliminate_suspect("Frank", chunk_index=5)
        assert record.eliminated_at == 3  # keeps original elimination point

    def test_active_after_elimination(self, tracker):
        tracker.introduce_suspect("A", chunk_index=0)
        tracker.introduce_suspect("B", chunk_index=1)
        tracker.eliminate_suspect("B", chunk_index=3)
        assert len(tracker.active_suspects) == 1
        assert tracker.active_suspects[0].name == "A"


class TestEvidenceAnnotation:
    def test_add_implicating_evidence(self, tracker):
        note = tracker.implicate("Richard", chunk_index=3, note="had motive")
        assert note.evidence_type == EvidenceType.IMPLICATES
        assert note.character == "Richard"
        assert note.chunk_index == 3
        assert note.note == "had motive"

    def test_add_clearing_evidence(self, tracker):
        note = tracker.clear("Frank", chunk_index=4, note="alibi confirmed")
        assert note.evidence_type == EvidenceType.CLEARS
        assert note.character == "Frank"

    def test_evidence_stored_on_timeline(self, tracker):
        tracker.implicate("A", chunk_index=1)
        tracker.clear("B", chunk_index=2)
        assert len(tracker.timeline.evidence) == 2

    def test_evidence_for_chunk(self, tracker):
        tracker.implicate("A", chunk_index=1, note="suspicious")
        tracker.clear("B", chunk_index=2, note="alibi")
        tracker.implicate("C", chunk_index=1, note="also suspicious")

        chunk_1_evidence = tracker.evidence_for_chunk(1)
        assert len(chunk_1_evidence) == 2
        assert all(e.chunk_index == 1 for e in chunk_1_evidence)


class TestStateReconstruction:
    def test_get_state_at_chunk(self, tracker):
        tracker.introduce_suspect("Alice", chunk_index=0)
        tracker.introduce_suspect("Bob", chunk_index=1)
        tracker.introduce_suspect("Charlie", chunk_index=3)
        tracker.eliminate_suspect("Alice", chunk_index=4)

        # At chunk 2: Alice and Bob active, Charlie not yet introduced
        states = tracker.get_state_at(2)
        assert states == {
            "Alice": SuspectState.ACTIVE,
            "Bob": SuspectState.ACTIVE,
        }

        # At chunk 4: Alice eliminated, Bob active, Charlie active
        states = tracker.get_state_at(4)
        assert states == {
            "Alice": SuspectState.ELIMINATED,
            "Bob": SuspectState.ACTIVE,
            "Charlie": SuspectState.ACTIVE,
        }

    def test_get_state_at_chunk_after_reactivation(self, tracker):
        tracker.introduce_suspect("Alice", chunk_index=0)
        tracker.eliminate_suspect("Alice", chunk_index=2)
        tracker.introduce_suspect("Alice", chunk_index=4)

        assert tracker.get_state_at(1) == {"Alice": SuspectState.ACTIVE}
        assert tracker.get_state_at(3) == {"Alice": SuspectState.ELIMINATED}
        assert tracker.get_state_at(4) == {"Alice": SuspectState.ACTIVE}


class TestSummary:
    def test_summary_output(self, tracker):
        tracker.introduce_suspect("Richard", chunk_index=1)
        tracker.introduce_suspect("Frank", chunk_index=2)
        tracker.eliminate_suspect("Frank", chunk_index=4)
        tracker.implicate("Richard", chunk_index=3, note="had motive")

        summary = tracker.summary()
        assert "Test Episode" in summary
        assert "Richard" in summary
        assert "Frank" in summary
        assert "Active suspects: 1" in summary
        assert "Eliminated suspects: 1" in summary
