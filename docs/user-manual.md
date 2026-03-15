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

For manual step-by-step inspection, the preferred numbered layout is:

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

## Transcript Inputs

Place plain-text episode transcripts in:

```text
<data-dir>/transcripts/
```

Supported transcript patterns today:
- screenplay-style transcripts with `INT.` / `EXT.` slug lines
- continuous-text transcripts that need boilerplate stripping and fixed-size chunking

The same CLI tools are meant to run against either committed
`test-run/01-transcripts/` data or your private local transcript folders. The
difference should be the path arguments you pass, not a separate test-only toolchain.

## Build Chunk Files

Generate chunked transcript payloads with:

```bash
PYTHONPATH=src python3 scripts/build_episode_timeline_chunks.py \
  --run-root test-run
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
- `--run-root`: derive numbered stage folders from a run root like `test-run` or `local-run`
- `--transcripts-dir`: override the transcript source directory
- `--output-dir`: override the chunk output directory
- `--chunk-size`: set the fixed chunk size for continuous-text transcripts

With `--run-root test-run`, the chunk output goes to:

```text
test-run/02-chunks/
```

## Run Codex CLI Inference

Build timeline JSON files from chunk files with:

```bash
PYTHONPATH=src python3 scripts/infer_timelines_with_codex_cli.py \
  --run-root test-run \
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
- `--run-root`: derive numbered stage folders from a run root like `test-run` or `local-run`
- `--file`: process a single `*.chunks.json` file
- `--max-chunks`: limit processing for a quick experiment
- `--retries`: retry invalid model output per chunk
- `--sleep-seconds`: pause between chunk calls

With `--run-root test-run`, the timeline output goes to:

```text
test-run/03-timelines/
```

Example single-episode run:

```bash
PYTHONPATH=src python3 scripts/infer_timelines_with_codex_cli.py \
  --run-root local-run \
  --max-chunks 5 \
  --codex-command "codex exec -"
```

## Run QC Checks

Check generated timeline files for obvious issues with:

```bash
PYTHONPATH=src python3 scripts/qc_timelines.py \
  --run-root test-run
```

Useful options:
- `--run-root`: derive numbered stage folders from a run root like `test-run` or `local-run`
- `--max-error-rate`: flag episodes above a chosen error threshold
- `--report-path`: write a JSON QC summary report

With `--run-root test-run`, the default report path is:

```text
test-run/04-qc/report.json
```

## Render HTML Visualizations

Generate self-contained HTML charts with:

```bash
PYTHONPATH=src python3 scripts/plot_timeline.py \
  --run-root test-run
```

Useful options:
- `--run-root`: derive numbered stage folders from a run root like `test-run` or `local-run`
- `--limit`: render only the first N episodes

With `--run-root test-run`, the HTML output goes to:

```text
test-run/05-html/
```

## Expected Outputs

In the numbered run-tree layout:
- `01-transcripts/*.txt`: raw transcript inputs
- `02-chunks/*.chunks.json`: ordered transcript chunks
- `03-timelines/*.timeline.json`: inferred suspect timelines
- `04-qc/report.json`: QC report output by default when using `--run-root`
- `05-html/*.html`: rendered episode charts plus `index.html`

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
