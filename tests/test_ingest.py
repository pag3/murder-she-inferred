"""Tests for transcript ingestion (FR-1)."""

import pytest
from pathlib import Path

from murder_she_inferred.ingest import (
    load_transcript,
    split_into_chunks,
    ingest_episode,
)
from murder_she_inferred.models import EpisodeMetadata


class TestLoadTranscript:
    def test_loads_file(self, sample_transcript_file):
        text = load_transcript(sample_transcript_file)
        assert "Jessica Fletcher" in text
        assert "FADE IN:" in text

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_transcript(tmp_path / "nonexistent.txt")


class TestSplitIntoChunks:
    def test_scene_mode(self, sample_transcript_text):
        chunks = split_into_chunks(sample_transcript_text, mode="scene")
        assert len(chunks) > 1
        # Each chunk should be a non-empty scene block
        for chunk in chunks:
            assert chunk.text.strip()
        # Indices should be sequential starting from 0
        assert [c.index for c in chunks] == list(range(len(chunks)))

    def test_line_mode(self, sample_transcript_text):
        chunks = split_into_chunks(sample_transcript_text, mode="line")
        assert len(chunks) > 1
        # Line mode should produce more chunks than scene mode
        scene_chunks = split_into_chunks(sample_transcript_text, mode="scene")
        assert len(chunks) > len(scene_chunks)

    def test_invalid_mode_raises(self, sample_transcript_text):
        with pytest.raises(ValueError, match="Unknown chunk mode"):
            split_into_chunks(sample_transcript_text, mode="invalid")

    def test_empty_text(self):
        chunks = split_into_chunks("", mode="scene")
        assert chunks == []

    def test_preserves_order(self, sample_transcript_text):
        chunks = split_into_chunks(sample_transcript_text, mode="scene")
        # FADE IN should be in an early chunk
        assert "FADE IN" in chunks[0].text
        # FADE OUT should be in the last chunk
        assert "FADE OUT" in chunks[-1].text


class TestIngestEpisode:
    def test_basic_ingestion(self, sample_transcript_file):
        timeline = ingest_episode(sample_transcript_file)
        assert len(timeline.chunks) > 0
        assert timeline.metadata.title == sample_transcript_file.stem
        assert timeline.suspects == {}
        assert timeline.evidence == []

    def test_with_metadata(self, sample_transcript_file):
        meta = EpisodeMetadata(
            title="The Murder of Sherlock Holmes",
            season=1,
            episode=1,
            year=1984,
        )
        timeline = ingest_episode(sample_transcript_file, metadata=meta)
        assert timeline.metadata.title == "The Murder of Sherlock Holmes"
        assert timeline.metadata.season == 1

    def test_line_mode(self, sample_transcript_file):
        timeline = ingest_episode(sample_transcript_file, chunk_mode="line")
        scene_timeline = ingest_episode(sample_transcript_file, chunk_mode="scene")
        assert len(timeline.chunks) > len(scene_timeline.chunks)
