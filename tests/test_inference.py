"""Tests for inference prompt building, JSON extraction, and result normalization."""

from __future__ import annotations

import json

import pytest

from typing import Callable

from murder_she_inferred.inference import (
    SYSTEM_PROMPT,
    build_prompt,
    build_timeline,
    extract_json_object,
    normalize_result,
)


class TestExtractJsonObject:
    def test_valid_json(self):
        raw = '{"introduced": ["Alice"], "eliminated": []}'
        result = extract_json_object(raw)
        assert result == {"introduced": ["Alice"], "eliminated": []}

    def test_markdown_wrapped(self):
        raw = '```json\n{"introduced": ["Bob"]}\n```'
        result = extract_json_object(raw)
        assert result == {"introduced": ["Bob"]}

    def test_json_with_surrounding_text(self):
        raw = 'Here is the result: {"introduced": ["Charlie"]} end of output'
        result = extract_json_object(raw)
        assert result == {"introduced": ["Charlie"]}

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="Empty response"):
            extract_json_object("")

    def test_no_json_raises(self):
        with pytest.raises(ValueError, match="Could not find JSON"):
            extract_json_object("no json here at all")


class TestNormalizeResult:
    def test_valid_payload(self):
        payload = {
            "introduced": ["Alice"],
            "eliminated": ["Bob"],
            "evidence": [
                {"type": "implicates", "character": "Alice", "note": "motive"},
                {"type": "clears", "character": "Bob", "note": "alibi"},
            ],
            "suspicion_scores": {"Alice": 80, "Charlie": 20},
        }
        result = normalize_result(payload)
        assert result["introduced"] == ["Alice"]
        assert result["eliminated"] == ["Bob"]
        assert len(result["evidence"]) == 2
        assert result["suspicion_scores"] == {"Alice": 80, "Charlie": 20}

    def test_missing_fields_default_empty(self):
        result = normalize_result({})
        assert result["introduced"] == []
        assert result["eliminated"] == []
        assert result["evidence"] == []
        assert result["suspicion_scores"] == {}

    def test_bad_evidence_type_filtered(self):
        payload = {
            "evidence": [
                {"type": "unknown_type", "character": "Alice", "note": "bad"},
                {"type": "implicates", "character": "Bob", "note": "good"},
            ],
        }
        result = normalize_result(payload)
        assert len(result["evidence"]) == 1
        assert result["evidence"][0]["character"] == "Bob"

    def test_score_clamping(self):
        payload = {"suspicion_scores": {"Alice": 150, "Bob": -10}}
        result = normalize_result(payload)
        assert result["suspicion_scores"]["Alice"] == 100
        assert result["suspicion_scores"]["Bob"] == 0

    def test_non_list_fields_default_empty(self):
        payload = {"introduced": "not a list", "eliminated": 42}
        result = normalize_result(payload)
        assert result["introduced"] == []
        assert result["eliminated"] == []


class TestBuildPrompt:
    def test_includes_system_prompt(self):
        prompt = build_prompt(
            episode_id="s01e01",
            chunk_index=0,
            context_text="context",
            current_chunk_text="chunk",
            active_suspects=[],
            eliminated_suspects=[],
        )
        assert SYSTEM_PROMPT in prompt

    def test_includes_prior_state(self):
        prompt = build_prompt(
            episode_id="s01e01",
            chunk_index=2,
            context_text="context",
            current_chunk_text="chunk",
            active_suspects=["Alice"],
            eliminated_suspects=["Bob"],
        )
        state = json.loads(
            prompt.split("Prior state:\n")[1].split("\n\nRecent transcript context:")[0]
        )
        assert state["episode_id"] == "s01e01"
        assert state["chunk_index"] == 2
        assert state["active_suspects"] == ["Alice"]
        assert state["eliminated_suspects"] == ["Bob"]

    def test_includes_context(self):
        prompt = build_prompt(
            episode_id="s01e01",
            chunk_index=0,
            context_text="Some transcript context here",
            current_chunk_text="chunk",
            active_suspects=[],
            eliminated_suspects=[],
        )
        assert "Some transcript context here" in prompt

    def test_includes_current_chunk(self):
        prompt = build_prompt(
            episode_id="s01e01",
            chunk_index=0,
            context_text="context",
            current_chunk_text="The butler did it",
            active_suspects=[],
            eliminated_suspects=[],
        )
        assert "The butler did it" in prompt

    def test_includes_prior_scores(self):
        prompt = build_prompt(
            episode_id="s01e01",
            chunk_index=1,
            context_text="context",
            current_chunk_text="chunk",
            active_suspects=["Alice"],
            eliminated_suspects=[],
            prior_scores={"Alice": 100},
        )
        state = json.loads(
            prompt.split("Prior state:\n")[1].split("\n\nRecent transcript context:")[0]
        )
        assert state["prior_suspicion_scores"] == {"Alice": 100}


class TestBuildTimeline:
    """Integration tests for build_timeline with mock backends."""

    @staticmethod
    def _make_chunks_payload(num_chunks: int = 3) -> dict:
        """Create a minimal chunks payload for testing."""
        return {
            "episode_id": "S01E01_test",
            "source_file": "test.txt",
            "chunk_mode": "fixed",
            "chunks": [
                {"index": i, "text": f"Chunk {i} text content."}
                for i in range(num_chunks)
            ],
        }

    @staticmethod
    def _make_mock_backend(responses: list[dict]) -> Callable[[str], str]:
        """Create a mock backend that returns canned JSON responses in order."""
        call_count = [0]

        def _backend(prompt: str) -> str:
            idx = min(call_count[0], len(responses) - 1)
            call_count[0] += 1
            return json.dumps(responses[idx])

        return _backend

    def test_basic_timeline_structure(self):
        """A mock backend producing valid responses yields correct timeline."""
        responses = [
            {
                "introduced": ["Alice", "Bob"],
                "eliminated": [],
                "evidence": [{"type": "implicates", "character": "Alice", "note": "seen near crime"}],
                "suspicion_scores": {"Alice": 60, "Bob": 40},
            },
            {
                "introduced": ["Charlie"],
                "eliminated": [],
                "evidence": [],
                "suspicion_scores": {"Alice": 50, "Bob": 30, "Charlie": 20},
            },
            {
                "introduced": [],
                "eliminated": ["Bob"],
                "evidence": [{"type": "clears", "character": "Bob", "note": "has alibi"}],
                "suspicion_scores": {"Alice": 65, "Charlie": 35},
            },
        ]
        payload = self._make_chunks_payload(3)
        backend = self._make_mock_backend(responses)

        result = build_timeline(
            payload,
            backend_fn=backend,
            max_chunks=None,
            context_window=5,
            retries=0,
            sleep_seconds=0.0,
        )

        assert result["episode_id"] == "S01E01_test"
        assert result["chunk_count"] == 3
        assert len(result["events"]) == 3
        assert "Bob" in result["final_eliminated_suspects"]
        assert "Alice" in result["final_active_suspects"]
        assert "Charlie" in result["final_active_suspects"]
        assert result["total_evidence_notes"] == 2

    def test_empty_chunks(self):
        """An episode with no chunks produces empty timeline."""
        payload = self._make_chunks_payload(0)
        backend = self._make_mock_backend([])

        result = build_timeline(
            payload,
            backend_fn=backend,
            max_chunks=None,
            context_window=5,
            retries=0,
            sleep_seconds=0.0,
        )

        assert result["chunk_count"] == 0
        assert result["events"] == []
        assert result["final_active_suspects"] == []
        assert result["final_eliminated_suspects"] == []

    def test_max_chunks_limits_processing(self):
        """max_chunks caps how many chunks are processed."""
        responses = [
            {"introduced": ["Alice"], "eliminated": [], "evidence": [], "suspicion_scores": {"Alice": 100}},
        ]
        payload = self._make_chunks_payload(5)
        backend = self._make_mock_backend(responses)

        result = build_timeline(
            payload,
            backend_fn=backend,
            max_chunks=2,
            context_window=5,
            retries=0,
            sleep_seconds=0.0,
        )

        assert result["chunk_count"] == 2
        assert len(result["events"]) == 2

    def test_backend_failure_uses_empty_result(self):
        """When backend raises on all retries, event has empty result."""
        def failing_backend(prompt: str) -> str:
            raise RuntimeError("Connection refused")

        payload = self._make_chunks_payload(1)

        result = build_timeline(
            payload,
            backend_fn=failing_backend,
            max_chunks=None,
            context_window=5,
            retries=1,
            sleep_seconds=0.0,
        )

        assert len(result["events"]) == 1
        event = result["events"][0]
        assert event["introduced"] == []
        assert event["eliminated"] == []
        assert event["error"] != ""

    def test_suspect_reactivation(self):
        """A previously eliminated suspect can be reintroduced."""
        responses = [
            {"introduced": ["Alice"], "eliminated": [], "evidence": [], "suspicion_scores": {"Alice": 100}},
            {"introduced": [], "eliminated": ["Alice"], "evidence": [], "suspicion_scores": {}},
            {"introduced": ["Alice"], "eliminated": [], "evidence": [], "suspicion_scores": {"Alice": 100}},
        ]
        payload = self._make_chunks_payload(3)
        backend = self._make_mock_backend(responses)

        result = build_timeline(
            payload,
            backend_fn=backend,
            max_chunks=None,
            context_window=5,
            retries=0,
            sleep_seconds=0.0,
        )

        assert "Alice" in result["final_active_suspects"]
        assert "Alice" not in result["final_eliminated_suspects"]

    def test_event_structure(self):
        """Each event has all required keys."""
        responses = [
            {"introduced": ["Alice"], "eliminated": [], "evidence": [], "suspicion_scores": {"Alice": 100}},
        ]
        payload = self._make_chunks_payload(1)
        backend = self._make_mock_backend(responses)

        result = build_timeline(
            payload,
            backend_fn=backend,
            max_chunks=None,
            context_window=5,
            retries=0,
            sleep_seconds=0.0,
        )

        event = result["events"][0]
        required_keys = {
            "chunk_index", "introduced", "eliminated", "evidence",
            "suspicion_scores", "active_suspects_after_chunk",
            "eliminated_suspects_after_chunk", "error",
        }
        assert required_keys.issubset(event.keys())
