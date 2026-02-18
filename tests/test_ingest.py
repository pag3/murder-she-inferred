"""Tests for transcript ingestion (FR-1)."""

import pytest
from pathlib import Path

from murder_she_inferred.ingest import (
    load_transcript,
    split_into_chunks,
    strip_boilerplate,
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


class TestStripBoilerplate:
    def test_strips_header(self, webtext_transcript_text):
        cleaned = strip_boilerplate(webtext_transcript_text)
        assert "Transcripts -" not in cleaned
        assert "Posted:" not in cleaned
        assert "bunniefuu" not in cleaned

    def test_strips_footer(self, webtext_transcript_text):
        cleaned = strip_boilerplate(webtext_transcript_text)
        assert "Powered by" not in cleaned
        assert "All times are UTC" not in cleaned

    def test_preserves_transcript_content(self, webtext_transcript_text):
        cleaned = strip_boilerplate(webtext_transcript_text)
        assert "I'm not particularly proud" in cleaned
        assert "Howard" in cleaned
        assert "Drake" in cleaned

    def test_no_boilerplate_returns_unchanged(self):
        text = "Just some plain transcript text. Nothing fancy here."
        cleaned = strip_boilerplate(text)
        assert cleaned == text

    def test_only_header_stripped(self):
        text = (
            "Site Name Posted: 01/15/23 09:00 by someone "
            "The actual transcript content starts here."
        )
        cleaned = strip_boilerplate(text)
        assert "Site Name" not in cleaned
        assert "The actual transcript content starts here." in cleaned


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


class TestFixedModeChunking:
    def test_short_text_single_chunk(self):
        text = "A short transcript that fits in one chunk."
        chunks = split_into_chunks(text, mode="fixed", chunk_size=500)
        assert len(chunks) == 1
        assert chunks[0].text == text

    def test_empty_text(self):
        chunks = split_into_chunks("", mode="fixed")
        assert chunks == []

    def test_splits_long_text(self):
        # Build a long text that needs splitting
        sentences = ["This is sentence number %d." % i for i in range(100)]
        text = " ".join(sentences)
        chunks = split_into_chunks(text, mode="fixed", chunk_size=200)
        assert len(chunks) > 1
        # Reassembled text should contain all original content
        reassembled = " ".join(c.text for c in chunks)
        for s in sentences:
            assert s in reassembled

    def test_respects_sentence_boundaries(self):
        text = (
            "First sentence here. Second sentence here. "
            "Third sentence here. Fourth sentence here. "
            "Fifth sentence here. Sixth sentence here."
        )
        chunks = split_into_chunks(text, mode="fixed", chunk_size=60)
        # Each chunk should end at a sentence boundary (period)
        for chunk in chunks[:-1]:  # last chunk may not end with period
            assert chunk.text.rstrip()[-1] == "."

    def test_sequential_indices(self):
        text = "Word. " * 500
        chunks = split_into_chunks(text, mode="fixed", chunk_size=100)
        assert [c.index for c in chunks] == list(range(len(chunks)))

    def test_no_empty_chunks(self):
        text = "Word. " * 500
        chunks = split_into_chunks(text, mode="fixed", chunk_size=100)
        for chunk in chunks:
            assert chunk.text.strip()

    def test_continuous_text_chunking(self, webtext_transcript_text):
        cleaned = strip_boilerplate(webtext_transcript_text)
        chunks = split_into_chunks(cleaned, mode="fixed", chunk_size=400)
        assert len(chunks) > 1
        # Content should be preserved
        reassembled = " ".join(c.text for c in chunks)
        assert "Howard" in reassembled
        assert "Drake" in reassembled


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

    def test_fixed_mode_ingestion(self, webtext_transcript_file):
        timeline = ingest_episode(
            webtext_transcript_file,
            chunk_mode="fixed",
            strip_boilerplate_text=True,
            chunk_size=400,
        )
        assert len(timeline.chunks) > 1
        # Boilerplate should be gone from chunks
        all_text = " ".join(c.text for c in timeline.chunks)
        assert "Powered by" not in all_text
        assert "Howard" in all_text

    def test_strip_boilerplate_flag(self, webtext_transcript_file):
        # Without stripping — boilerplate is present
        timeline_raw = ingest_episode(
            webtext_transcript_file, chunk_mode="fixed", chunk_size=5000
        )
        raw_text = " ".join(c.text for c in timeline_raw.chunks)
        assert "Transcripts" in raw_text

        # With stripping — boilerplate is removed
        timeline_clean = ingest_episode(
            webtext_transcript_file,
            chunk_mode="fixed",
            strip_boilerplate_text=True,
            chunk_size=5000,
        )
        clean_text = " ".join(c.text for c in timeline_clean.chunks)
        assert "Transcripts -" not in clean_text
