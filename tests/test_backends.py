"""Tests for murder_she_inferred.backends."""
from __future__ import annotations

import json

import pytest

from murder_she_inferred.backends import (
    codex_cli_backend,
    openai_http_backend,
    _normalize_codex_command,
)


class TestNormalizeCodexCommand:
    def test_bare_codex_gets_exec_dash(self):
        assert _normalize_codex_command("codex") == "codex exec -"

    def test_full_command_unchanged(self):
        assert _normalize_codex_command("codex exec -") == "codex exec -"

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="empty"):
            _normalize_codex_command("")


class TestCodexCliBackend:
    def test_returns_stdout(self, monkeypatch):
        import subprocess as sp

        def fake_run(cmd, **kwargs):
            result = sp.CompletedProcess(args=cmd, returncode=0, stdout='{"introduced": []}', stderr="")
            return result

        monkeypatch.setattr("murder_she_inferred.backends.subprocess.run", fake_run)
        backend = codex_cli_backend("echo")
        assert backend("test prompt") == '{"introduced": []}'

    def test_nonzero_exit_raises(self, monkeypatch):
        import subprocess as sp

        def fake_run(cmd, **kwargs):
            return sp.CompletedProcess(args=cmd, returncode=1, stdout="", stderr="error msg")

        monkeypatch.setattr("murder_she_inferred.backends.subprocess.run", fake_run)
        backend = codex_cli_backend("echo")
        with pytest.raises(RuntimeError, match="Codex command failed"):
            backend("test prompt")


class TestOpenaiHttpBackend:
    def _mock_urlopen(self, monkeypatch, response_body: dict, status: int = 200):
        """Helper to mock urllib.request.urlopen."""
        import io

        class FakeResponse:
            def __init__(self, data, code):
                self._data = json.dumps(data).encode("utf-8")
                self.status = code
            def read(self):
                return self._data
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass

        def fake_urlopen(req, timeout=None):
            return FakeResponse(response_body, status)

        monkeypatch.setattr("murder_she_inferred.backends.urllib.request.urlopen", fake_urlopen)

    def test_parses_valid_response(self, monkeypatch):
        self._mock_urlopen(monkeypatch, {
            "choices": [{"message": {"content": '{"introduced": ["Alice"]}'}}]
        })
        backend = openai_http_backend(api_url="http://localhost:11434/v1/chat/completions", model="test")
        result = backend("test prompt")
        assert '"Alice"' in result

    def test_bad_response_format_raises(self, monkeypatch):
        self._mock_urlopen(monkeypatch, {"unexpected": "format"})
        backend = openai_http_backend()
        with pytest.raises(RuntimeError, match="Unexpected response format"):
            backend("test prompt")

    def test_http_error_raises(self, monkeypatch):
        import urllib.error

        def fake_urlopen(req, timeout=None):
            raise urllib.error.HTTPError(
                url="http://localhost", code=500, msg="Server Error",
                hdrs=None, fp=__import__("io").BytesIO(b"internal error")
            )

        monkeypatch.setattr("murder_she_inferred.backends.urllib.request.urlopen", fake_urlopen)
        backend = openai_http_backend()
        with pytest.raises(RuntimeError, match="HTTP 500"):
            backend("test prompt")

    def test_connection_error_raises(self, monkeypatch):
        import urllib.error

        def fake_urlopen(req, timeout=None):
            raise urllib.error.URLError("Connection refused")

        monkeypatch.setattr("murder_she_inferred.backends.urllib.request.urlopen", fake_urlopen)
        backend = openai_http_backend()
        with pytest.raises(RuntimeError, match="Could not connect"):
            backend("test prompt")

    def test_sends_system_and_user_messages(self, monkeypatch):
        """Verify the request body separates system prompt from user content."""
        captured_requests = []

        class FakeResponse:
            def read(self):
                return json.dumps({
                    "choices": [{"message": {"content": "ok"}}]
                }).encode("utf-8")
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass

        def fake_urlopen(req, timeout=None):
            captured_requests.append(json.loads(req.data.decode("utf-8")))
            return FakeResponse()

        monkeypatch.setattr("murder_she_inferred.backends.urllib.request.urlopen", fake_urlopen)
        backend = openai_http_backend(model="test-model")

        from murder_she_inferred.inference import SYSTEM_PROMPT
        full_prompt = SYSTEM_PROMPT + "\n\nPrior state:\n{}\n\nCurrent chunk text:\ntest"
        backend(full_prompt)

        assert len(captured_requests) == 1
        body = captured_requests[0]
        assert body["model"] == "test-model"
        assert len(body["messages"]) == 2
        assert body["messages"][0]["role"] == "system"
        assert body["messages"][0]["content"] == SYSTEM_PROMPT
        assert body["messages"][1]["role"] == "user"
