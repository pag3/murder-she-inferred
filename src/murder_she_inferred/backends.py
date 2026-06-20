"""Inference backends for murder-she-inferred.

Each backend factory returns a callable with signature (prompt: str) -> str
that sends a prompt to an LLM and returns the raw text response.
"""
from __future__ import annotations

import json
import shlex
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from typing import Callable


def codex_cli_backend(command: str = "codex exec -") -> Callable[[str], str]:
    """Return a backend that calls the Codex CLI via subprocess.

    Args:
        command: Shell command for Codex CLI. Prompt is sent on stdin.
    """
    command = _normalize_codex_command(command)

    def _call(prompt: str) -> str:
        completed = subprocess.run(
            command,
            shell=True,
            input=prompt,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                f"Codex command failed ({completed.returncode}): {completed.stderr.strip()}"
            )
        return completed.stdout

    return _call


def openai_http_backend(
    api_url: str = "http://localhost:11434/v1/chat/completions",
    model: str = "llama3",
    timeout: float = 120.0,
) -> Callable[[str], str]:
    """Return a backend that calls an OpenAI-compatible chat completions endpoint.

    Works with Ollama, llama.cpp, LM Studio, OpenVINO, or any server exposing
    the /v1/chat/completions API.

    Args:
        api_url: Full URL to the chat completions endpoint.
        model: Model name to request.
        timeout: Request timeout in seconds.
    """
    def _call(prompt: str) -> str:
        # Import SYSTEM_PROMPT here to split system vs user message
        from murder_she_inferred.inference import SYSTEM_PROMPT

        # The prompt from build_prompt starts with SYSTEM_PROMPT + "\n\n"
        # then has the rest as user content. Split them.
        user_content = prompt
        if prompt.startswith(SYSTEM_PROMPT):
            user_content = prompt[len(SYSTEM_PROMPT):].lstrip("\n")

        request_body = json.dumps({
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.2,
        }).encode("utf-8")

        req = urllib.request.Request(
            api_url,
            data=request_body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise RuntimeError(
                f"HTTP {exc.code} from {api_url}: {exc.read().decode('utf-8', errors='replace')}"
            ) from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"Could not connect to {api_url}: {exc.reason}"
            ) from exc

        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(
                f"Unexpected response format from {api_url}: {data}"
            ) from exc

    return _call


def _normalize_codex_command(command: str) -> str:
    """Ensure Codex command runs in non-interactive mode."""
    parts = shlex.split(command)
    if not parts:
        raise ValueError("codex command is empty")
    binary = Path(parts[0]).name
    if binary == "codex" and len(parts) == 1:
        return f"{command} exec -"
    return command
