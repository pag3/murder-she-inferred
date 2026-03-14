# User Manual

This guide covers the current supported workflow for generating suspect
timelines from local episode transcripts.

## Data Directory

The project expects a local data directory for inputs and generated artifacts.

- Default location: `../murder-she-inferred-data`
- Override with `MURDER_SHE_INFERRED_DATA_DIR` in a project-local `.env`

Create `.env` from the example file:

```bash
cp .env.example .env
```

A typical data directory layout looks like this:

```text
murder-she-inferred-data/
  transcripts/
  episode_timeline_chunks/
  episode_timelines_codex_cli/
  timeline_qc/
  timeline_html/
```

Only `transcripts/` needs to exist up front. The scripts create output
directories as needed.

## Transcript Inputs

Place plain-text episode transcripts in:

```text
<data-dir>/transcripts/
```

Supported transcript patterns today:
- screenplay-style transcripts with `INT.` / `EXT.` slug lines
- continuous-text transcripts that need boilerplate stripping and fixed-size chunking

## Build Chunk Files

Generate chunked transcript payloads with:

```bash
PYTHONPATH=src python3 scripts/build_episode_timeline_chunks.py
```

By default this reads from:

```text
<data-dir>/transcripts/
```

and writes chunk files to:

```text
<data-dir>/episode_timeline_chunks/
```

Useful options:
- `--transcripts-dir`: override the transcript source directory
- `--output-dir`: override the chunk output directory
- `--chunk-size`: set the fixed chunk size for continuous-text transcripts

## Run Codex CLI Inference

Build timeline JSON files from chunk files with:

```bash
PYTHONPATH=src python3 scripts/infer_timelines_with_codex_cli.py \
  --codex-command "codex exec -"
```

By default this reads chunk files from:

```text
<data-dir>/episode_timeline_chunks/
```

and writes timeline files to:

```text
<data-dir>/episode_timelines_codex_cli/
```

Useful options:
- `--file`: process a single `*.chunks.json` file
- `--max-chunks`: limit processing for a quick experiment
- `--retries`: retry invalid model output per chunk
- `--sleep-seconds`: pause between chunk calls
- `--prompt-profile`: choose `baseline` or `strict_elimination`

Example single-episode run:

```bash
PYTHONPATH=src python3 scripts/infer_timelines_with_codex_cli.py \
  --file "../murder-she-inferred-data/episode_timeline_chunks/S01E03 - 01x03 - Deadly Lady.chunks.json" \
  --max-chunks 5 \
  --codex-command "codex exec -" \
  --prompt-profile baseline
```

## Run QC Checks

Check generated timeline files for obvious issues with:

```bash
PYTHONPATH=src python3 scripts/qc_timelines.py \
  --input-dir "../murder-she-inferred-data/episode_timelines_codex_cli"
```

Useful options:
- `--max-error-rate`: flag episodes above a chosen error threshold
- `--report-path`: write a JSON QC summary report

## Render HTML Visualizations

Generate self-contained HTML charts with:

```bash
PYTHONPATH=src python3 scripts/plot_timeline.py \
  --input-dir "../murder-she-inferred-data/episode_timelines_codex_cli" \
  --output-dir "../murder-she-inferred-data/timeline_html"
```

Useful options:
- `--limit`: render only the first N episodes

## Expected Outputs

- `episode_timeline_chunks/*.chunks.json`: ordered transcript chunks
- `episode_timelines_codex_cli/*.timeline.json`: inferred suspect timelines
- `timeline_qc/*.json`: optional QC reports if `--report-path` is used
- `timeline_html/*.html`: rendered episode charts

## Troubleshooting

If a script cannot find the data directory:
- create `.env`
- set `MURDER_SHE_INFERRED_DATA_DIR`
- or create the default sibling directory `../murder-she-inferred-data`

If chunk building fails:
- confirm transcript files end in `.txt`
- confirm they live under `<data-dir>/transcripts/`

If inference fails:
- confirm the `codex` CLI is installed and callable
- try `--max-chunks` on a single file first
- inspect any `error` fields in the generated timeline JSON

If plotting or QC fails:
- confirm timeline JSON files exist under the input directory you passed

