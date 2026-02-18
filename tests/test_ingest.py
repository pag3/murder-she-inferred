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
    def test_scene_mode_splits_on_slug_lines(self, sample_transcript_text):
        chunks = split_into_chunks(sample_transcript_text, mode="scene")
        # The sample transcript has 7 slug lines (INT./EXT.).
        # "FADE IN:" is trivial preamble and gets dropped.
        # "FADE OUT." is appended to the last scene.
        assert len(chunks) == 7
        # Each chunk should start with a slug line
        for chunk in chunks:
            assert chunk.text.startswith("INT.") or chunk.text.startswith("EXT.")
        # Indices should be sequential starting from 0
        assert [c.index for c in chunks] == list(range(len(chunks)))

    def test_scene_mode_groups_dialogue_into_scenes(self, sample_transcript_text):
        chunks = split_into_chunks(sample_transcript_text, mode="scene")
        # The marina scene (chunk 1) should contain all the dialogue
        # from Richard, Helen, Metzger, and Jessica at the marina
        marina_chunk = chunks[1]
        assert "INT. CABOT COVE MARINA" in marina_chunk.text
        assert "RICHARD:" in marina_chunk.text
        assert "HELEN:" in marina_chunk.text
        assert "METZGER:" in marina_chunk.text

    def test_scene_mode_last_chunk_has_fade_out(self, sample_transcript_text):
        chunks = split_into_chunks(sample_transcript_text, mode="scene")
        assert "FADE OUT" in chunks[-1].text

    def test_paragraph_mode(self, sample_transcript_text):
        chunks = split_into_chunks(sample_transcript_text, mode="paragraph")
        assert len(chunks) > 1
        # Paragraph mode produces more chunks than scene mode
        scene_chunks = split_into_chunks(sample_transcript_text, mode="scene")
        assert len(chunks) > len(scene_chunks)

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

    def test_preserves_scene_order(self, sample_transcript_text):
        chunks = split_into_chunks(sample_transcript_text, mode="scene")
        # First scene should be Jessica's house
        assert "JESSICA'S HOUSE" in chunks[0].text
        # Last scene should be Sheriff's office with the reveal
        assert "I think I know who did it" in chunks[-1].text

    def test_no_slug_lines_falls_back_to_paragraphs(self):
        text = "Block one.\n\nBlock two.\n\nBlock three."
        chunks = split_into_chunks(text, mode="scene")
        # No slug lines, so falls back to paragraph splitting
        assert len(chunks) == 3

    def test_nontrivial_preamble_kept(self):
        text = (
            "MURDER, SHE WROTE\n"
            "Season 1, Episode 1\n"
            '"The Murder of Sherlock Holmes"\n'
            "\n"
            "INT. JESSICA'S HOUSE - DAY\n"
            "\n"
            "Some dialogue here.\n"
        )
        chunks = split_into_chunks(text, mode="scene")
        # Preamble with episode info should be kept as chunk 0
        assert len(chunks) == 2
        assert "MURDER, SHE WROTE" in chunks[0].text
        assert "INT. JESSICA'S HOUSE" in chunks[1].text

    def test_trivial_preamble_dropped(self):
        text = (
            "FADE IN:\n"
            "\n"
            "INT. JESSICA'S HOUSE - DAY\n"
            "\n"
            "Some dialogue here.\n"
        )
        chunks = split_into_chunks(text, mode="scene")
        # "FADE IN:" is trivial and should be dropped
        assert len(chunks) == 1
        assert chunks[0].text.startswith("INT.")


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

    def test_scene_mode_produces_proper_scenes(self, sample_transcript_file):
        timeline = ingest_episode(sample_transcript_file, chunk_mode="scene")
        # Should have 7 scenes matching the 7 slug lines
        assert len(timeline.chunks) == 7
