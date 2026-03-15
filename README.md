# murder-she-inferred

Temporal inference of culpability in *Murder, She Wrote* using AI.

This project is a local-first prototype for turning episode transcripts into
suspect timelines. It chunks transcripts in order, asks an LLM for structured
suspect-state updates, tracks who remains viable over time, and renders the
results into reviewable outputs.

## Quickstart

1. Create a project-local environment file:

```bash
cp .env.example .env
```

2. Optionally set `MURDER_SHE_INFERRED_DATA_DIR` in `.env`.
   If unset, the project defaults to `../murder-she-inferred-data`.

3. Install the package and test dependencies:

```bash
python3 -m pip install -e '.[dev]'
```

4. Build transcript chunks:

```bash
PYTHONPATH=src python3 scripts/build_episode_timeline_chunks.py
```

5. Run Codex CLI inference:

```bash
PYTHONPATH=src python3 scripts/build_episode_timeline_chunks.py \
  --run-root test-run

PYTHONPATH=src python3 scripts/infer_timelines_with_codex_cli.py \
  --run-root test-run \
  --codex-command "codex exec -"
```

## Current State

The repository currently supports a working prototype pipeline for:
- local data directory configuration
- transcript chunk generation
- per-chunk Codex CLI inference into timeline JSON
- QC checks for generated timelines
- HTML visualization rendering

The intended design is to run the same CLI tools against either committed
`test-run/01-transcripts/` inputs or your private local transcript folders by
changing CLI path arguments, rather than maintaining separate test-only tools.

Preferred numbered run trees:

```text
test-run/
  01-transcripts/
  02-chunks/
  03-timelines/
  04-qc/
  05-html/

local-run/
  01-transcripts/
  02-chunks/
  03-timelines/
  04-qc/
  05-html/
```

The model-training path described in the project spec is future work and is not
implemented yet.

## Documentation

- [User Manual](docs/user-manual.md)
- [Project Spec](docs/spec.md)
- [Roadmap](docs/roadmap.md)
- [Contributing Guide](CONTRIBUTING.md)

## Repository Layout

- `src/murder_she_inferred/`: package code for ingestion, state tracking, and settings
- `scripts/`: entrypoints for chunk generation, inference, QC, and plotting
- `tests/`: automated test coverage for the current Python package
