"""Tests for committed synthetic test-transcripts."""

from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

from murder_she_inferred.ingest import load_transcript, split_into_chunks, strip_boilerplate


TRANSCRIPT_EXPECTATIONS = {
    "T01 - Harbor Ledger.txt": {
        "must_keep": ["Margo Dane", "Evan Pike", "Ruth Fallon"],
        "must_strip": ["Transcript Archive", "Powered by Example Forum Software", "Posted:"],
        "chunk_size": 500,
        "min_chunks": 1,
    },
    "T02 - Gallery Opening.txt": {
        "must_keep": ["Celia March", "Grant Heller", "Nina Vale"],
        "must_strip": ["Transcript Archive", "Powered by Example Forum Software", "Posted:"],
        "chunk_size": 500,
        "min_chunks": 2,
    },
    "T03 - Founders Weekend.txt": {
        "must_keep": ["Felix Dunn", "Vivian Shore", "Owen Pritchard"],
        "must_strip": ["Transcript Archive", "Powered by Example Forum Software", "Posted:"],
        "chunk_size": 500,
        "min_chunks": 10,
    },
    "T04 - Bell Tower Static.txt": {
        "must_keep": ["Pastor Len Mercer", "Doria Pike", "Theo Marsh"],
        "must_strip": ["Transcript Archive", "Powered by Example Forum Software", "Posted:"],
        "chunk_size": 450,
        "min_chunks": 8,
    },
    "T05 - Last Ferry Interview.txt": {
        "must_keep": ["Isla Voss", "Marcus Reed", "Paula Kent"],
        "must_strip": ["Transcript Archive", "Powered by Example Forum Software", "Posted:"],
        "chunk_size": 450,
        "min_chunks": 9,
    },
}


def test_committed_test_transcripts_are_present(synthetic_test_transcripts_dir: Path):
    paths = sorted(synthetic_test_transcripts_dir.glob("*.txt"))
    assert len(paths) == 5
    assert [path.name for path in paths] == sorted(TRANSCRIPT_EXPECTATIONS)


def test_test_transcripts_can_be_loaded_cleaned_and_chunked(
    synthetic_test_transcripts_dir: Path,
):
    for filename, expected in TRANSCRIPT_EXPECTATIONS.items():
        path = synthetic_test_transcripts_dir / filename
        raw_text = load_transcript(path)
        cleaned_text = strip_boilerplate(raw_text)

        for fragment in expected["must_strip"]:
            assert fragment not in cleaned_text

        for fragment in expected["must_keep"]:
            assert fragment in cleaned_text

        chunks_first = split_into_chunks(
            cleaned_text,
            mode="fixed",
            chunk_size=expected["chunk_size"],
        )
        chunks_second = split_into_chunks(
            cleaned_text,
            mode="fixed",
            chunk_size=expected["chunk_size"],
        )

        assert len(chunks_first) >= expected["min_chunks"]
        assert [chunk.index for chunk in chunks_first] == list(range(len(chunks_first)))
        assert all(chunk.text.strip() for chunk in chunks_first)
        assert [chunk.text for chunk in chunks_first] == [chunk.text for chunk in chunks_second]

        reassembled = " ".join(chunk.text for chunk in chunks_first)
        for fragment in expected["must_keep"]:
            assert fragment in reassembled


def test_build_episode_timeline_chunks_script_accepts_test_transcripts(
    synthetic_test_transcripts_dir: Path,
    tmp_path: Path,
):
    output_dir = tmp_path / "episode_timeline_chunks"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/build_episode_timeline_chunks.py",
            "--transcripts-dir",
            str(synthetic_test_transcripts_dir),
            "--output-dir",
            str(output_dir),
            "--chunk-size",
            "450",
        ],
        cwd=Path(__file__).resolve().parents[1],
        env={**os.environ, "PYTHONPATH": "src"},
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "Processed 5 transcripts" in result.stdout

    payload_paths = sorted(output_dir.glob("*.chunks.json"))
    assert len(payload_paths) == 5

    first_payload = json.loads(payload_paths[0].read_text(encoding="utf-8"))
    assert first_payload["chunk_mode"] == "fixed"
    assert first_payload["chunk_count"] >= 1
    assert first_payload["chunks"][0]["index"] == 0
    assert "Transcript Archive" not in first_payload["chunks"][0]["text"]


def test_build_episode_timeline_chunks_supports_run_root(
    synthetic_test_transcripts_dir: Path,
    tmp_path: Path,
):
    repo_root = Path(__file__).resolve().parents[1]
    run_root = tmp_path / "run-root"
    transcripts_dir = run_root / "01-transcripts"
    shutil.copytree(synthetic_test_transcripts_dir, transcripts_dir)

    result = subprocess.run(
        [
            sys.executable,
            "scripts/build_episode_timeline_chunks.py",
            "--run-root",
            str(run_root),
            "--chunk-size",
            "450",
        ],
        cwd=repo_root,
        env={**os.environ, "PYTHONPATH": "src"},
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert (run_root / "02-chunks").exists()
    assert len(list((run_root / "02-chunks").glob("*.chunks.json"))) == 5


def test_explicit_stage_paths_override_run_root(
    synthetic_test_transcripts_dir: Path,
    tmp_path: Path,
):
    repo_root = Path(__file__).resolve().parents[1]
    run_root = tmp_path / "run-root"
    transcripts_dir = run_root / "01-transcripts"
    override_output_dir = tmp_path / "override-chunks"
    shutil.copytree(synthetic_test_transcripts_dir, transcripts_dir)

    result = subprocess.run(
        [
            sys.executable,
            "scripts/build_episode_timeline_chunks.py",
            "--run-root",
            str(run_root),
            "--output-dir",
            str(override_output_dir),
            "--chunk-size",
            "450",
        ],
        cwd=repo_root,
        env={**os.environ, "PYTHONPATH": "src"},
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert len(list(override_output_dir.glob("*.chunks.json"))) == 5
    assert not (run_root / "02-chunks").exists()


def test_run_root_requires_numbered_transcripts_folder(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[1]
    run_root = tmp_path / "run-root"
    run_root.mkdir()

    result = subprocess.run(
        [
            sys.executable,
            "scripts/build_episode_timeline_chunks.py",
            "--run-root",
            str(run_root),
        ],
        cwd=repo_root,
        env={**os.environ, "PYTHONPATH": "src"},
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "01-transcripts" in result.stderr


def test_pipeline_scripts_run_against_committed_test_transcripts(
    synthetic_test_transcripts_dir: Path,
    tmp_path: Path,
):
    repo_root = Path(__file__).resolve().parents[1]
    run_root = tmp_path / "run-root"
    transcripts_dir = run_root / "01-transcripts"
    timeline_dir = run_root / "03-timelines"
    html_dir = run_root / "05-html"
    qc_report = run_root / "04-qc" / "report.json"
    fake_codex = tmp_path / "fake_codex.py"
    shutil.copytree(synthetic_test_transcripts_dir, transcripts_dir)
    fake_codex.write_text(
        (
            "import json\n"
            "print(json.dumps({"
            "\"introduced\": [], "
            "\"eliminated\": [], "
            "\"evidence\": []"
            "}))\n"
        ),
        encoding="utf-8",
    )

    env = {**os.environ, "PYTHONPATH": "src"}

    build_result = subprocess.run(
        [
            sys.executable,
            "scripts/build_episode_timeline_chunks.py",
            "--run-root",
            str(run_root),
            "--chunk-size",
            "450",
        ],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert build_result.returncode == 0, build_result.stderr

    codex_command = f"{shlex.quote(sys.executable)} {shlex.quote(str(fake_codex))}"
    infer_result = subprocess.run(
        [
            sys.executable,
            "scripts/infer_timelines_with_codex_cli.py",
            "--run-root",
            str(run_root),
            "--codex-command",
            codex_command,
        ],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert infer_result.returncode == 0, infer_result.stderr
    assert "Processed episodes: 5" in infer_result.stdout

    qc_result = subprocess.run(
        [
            sys.executable,
            "scripts/qc_timelines.py",
            "--run-root",
            str(run_root),
        ],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert qc_result.returncode == 0, qc_result.stderr
    assert qc_report.exists()

    plot_result = subprocess.run(
        [
            sys.executable,
            "scripts/plot_timeline.py",
            "--run-root",
            str(run_root),
        ],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert plot_result.returncode == 0, plot_result.stderr

    chunk_paths = sorted((run_root / "02-chunks").glob("*.chunks.json"))
    timeline_paths = sorted(timeline_dir.glob("*.timeline.json"))
    html_paths = sorted(html_dir.glob("*.html"))
    assert len(chunk_paths) == 5
    assert len(timeline_paths) == 5
    assert len(html_paths) == 11
    assert (html_dir / "index.html").exists()
    assert len(list(html_dir.glob("*.timeline.html"))) == 5
    assert len(list(html_dir.glob("*.evidence.html"))) == 5
    first_evidence = sorted(html_dir.glob("*.evidence.html"))[0]
    assert "No evidence annotations yet." in first_evidence.read_text(encoding="utf-8")

    qc_payload = json.loads(qc_report.read_text(encoding="utf-8"))
    assert qc_payload["file_count"] == 5
    assert qc_payload["input_dir"] == str(timeline_dir)


def test_run_full_pipeline_script_runs_all_stages(
    synthetic_test_transcripts_dir: Path,
    tmp_path: Path,
):
    repo_root = Path(__file__).resolve().parents[1]
    run_root = tmp_path / "run-root"
    transcripts_dir = run_root / "01-transcripts"
    fake_codex = tmp_path / "fake_codex.py"
    shutil.copytree(synthetic_test_transcripts_dir, transcripts_dir)
    fake_codex.write_text(
        (
            "import json\n"
            "print(json.dumps({"
            "\"introduced\": [], "
            "\"eliminated\": [], "
            "\"evidence\": []"
            "}))\n"
        ),
        encoding="utf-8",
    )

    env = {**os.environ, "PYTHONPATH": "src"}
    codex_command = f"{shlex.quote(sys.executable)} {shlex.quote(str(fake_codex))}"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_full_pipeline.py",
            "--run-root",
            str(run_root),
            "--codex-command",
            codex_command,
            "--chunk-size",
            "450",
        ],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert (run_root / "02-chunks").exists()
    assert (run_root / "03-timelines").exists()
    assert (run_root / "04-qc" / "report.json").exists()
    assert (run_root / "05-html" / "index.html").exists()
    assert "Full pipeline completed" in result.stdout


def test_package_cli_runs_full_pipeline_without_explicit_subcommand(
    synthetic_test_transcripts_dir: Path,
    tmp_path: Path,
):
    repo_root = Path(__file__).resolve().parents[1]
    run_root = tmp_path / "run-root"
    transcripts_dir = run_root / "01-transcripts"
    fake_codex = tmp_path / "fake_codex.py"
    shutil.copytree(synthetic_test_transcripts_dir, transcripts_dir)
    fake_codex.write_text(
        (
            "import json\n"
            "print(json.dumps({"
            "\"introduced\": [], "
            "\"eliminated\": [], "
            "\"evidence\": []"
            "}))\n"
        ),
        encoding="utf-8",
    )

    env = {**os.environ, "PYTHONPATH": "src"}
    codex_command = f"{shlex.quote(sys.executable)} {shlex.quote(str(fake_codex))}"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "murder_she_inferred.cli",
            "--run-root",
            str(run_root),
            "--codex-command",
            codex_command,
            "--chunk-size",
            "450",
        ],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert (run_root / "02-chunks").exists()
    assert (run_root / "03-timelines").exists()
    assert (run_root / "04-qc" / "report.json").exists()
    assert (run_root / "05-html" / "index.html").exists()
    assert "Full pipeline completed" in result.stdout
