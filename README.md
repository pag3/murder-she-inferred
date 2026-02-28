# murder-she-inferred
Temporal inference of culpability in Murder, She Wrote using AI

## Local data directory (project-only)

Data can live outside this repo (for privacy), for example in the sibling folder:
`../murder-she-inferred-data`.

Configuration is project-local and does not require system-wide setup:

1. Create `.env` from `.env.example`
2. Set `MURDER_SHE_INFERRED_DATA_DIR` if needed

```bash
cp .env.example .env
```

In Python:

```python
from murder_she_inferred import get_data_dir, data_path

root = get_data_dir()
transcript = data_path("transcripts", "episode1.txt")
```

## Codex CLI inference prototype

This project includes an experimental pipeline that calls Codex CLI per chunk
and builds timeline outputs.
Each chunk inference receives cumulative context from episode start through the
current chunk (chunk 0..i), plus prior suspect state.

1. Build chunk files:

```bash
PYTHONPATH=src python3 scripts/build_episode_timeline_chunks.py
```

2. Run Codex CLI inference:

```bash
PYTHONPATH=src python3 scripts/infer_timelines_with_codex_cli.py \
  --codex-command "codex exec -"
```

By default, outputs are written to:
`../murder-she-inferred-data/episode_timelines_codex_cli`

You can test one episode first:

```bash
PYTHONPATH=src python3 scripts/infer_timelines_with_codex_cli.py \
  --file "../murder-she-inferred-data/episode_timeline_chunks/S01E03 - 01x03 - Deadly Lady.chunks.json" \
  --max-chunks 5 \
  --codex-command "codex exec -"
```
