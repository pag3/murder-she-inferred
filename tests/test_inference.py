"""Tests for inference prompt building, JSON extraction, and result normalization."""

from __future__ import annotations

import json

import pytest

from murder_she_inferred.inference import (
    SYSTEM_PROMPT,
    build_prompt,
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
