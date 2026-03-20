from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def test_plot_timeline_renders_state_heatmap_and_evidence_markers(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    input_dir = tmp_path / "03-timelines"
    output_dir = tmp_path / "05-html"
    input_dir.mkdir(parents=True)

    payload = {
        "episode_id": "S00E00 - Test Episode",
        "events": [
            {
                "chunk_index": 0,
                "introduced": [],
                "eliminated": [],
                "evidence": [],
                "active_suspects_after_chunk": [],
                "eliminated_suspects_after_chunk": [],
                "error": "",
            },
            {
                "chunk_index": 1,
                "introduced": ["Alice"],
                "eliminated": [],
                "evidence": [
                    {
                        "type": "implicates",
                        "character": "Alice",
                        "note": "A clue points toward Alice.",
                    }
                ],
                "active_suspects_after_chunk": ["Alice"],
                "eliminated_suspects_after_chunk": [],
                "error": "",
            },
            {
                "chunk_index": 2,
                "introduced": ["Bob"],
                "eliminated": [],
                "evidence": [
                    {
                        "type": "clears",
                        "character": "Alice",
                        "note": "Alice has an alibi.",
                    }
                ],
                "active_suspects_after_chunk": ["Alice", "Bob"],
                "eliminated_suspects_after_chunk": [],
                "error": "",
            },
            {
                "chunk_index": 3,
                "introduced": [],
                "eliminated": ["Alice"],
                "evidence": [],
                "active_suspects_after_chunk": ["Bob"],
                "eliminated_suspects_after_chunk": ["Alice"],
                "error": "",
            },
        ],
    }
    (input_dir / "test.timeline.json").write_text(json.dumps(payload), encoding="utf-8")

    env = {**os.environ, "PYTHONPATH": "src"}
    result = subprocess.run(
        [
            sys.executable,
            "scripts/plot_timeline.py",
            "--input-dir",
            str(input_dir),
            "--output-dir",
            str(output_dir),
        ],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr

    html_path = output_dir / "test.timeline.html"
    assert html_path.exists()
    html_text = html_path.read_text(encoding="utf-8")

    assert "Suspicion State Heatmap" in html_text
    assert "not introduced" in html_text
    assert "inactive after introduction" in html_text
    assert "implicates" in html_text
    assert "clears" in html_text
    assert "#c96d1a" in html_text
    assert "#157f6b" in html_text
    assert "Alice" in html_text
    assert "Bob" in html_text
