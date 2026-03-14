# Contributing

Thanks for helping improve `murder-she-inferred`.

## Local Setup

Install the project in editable mode with the development dependencies:

```bash
python3 -m pip install -e '.[dev]'
```

Most commands assume the repository root as the working directory.

If you need local transcript data, create a project-local `.env` file:

```bash
cp .env.example .env
```

Set `MURDER_SHE_INFERRED_DATA_DIR` in `.env` if your data lives somewhere
other than the default sibling directory `../murder-she-inferred-data`.

## Running Tests

Run the full test suite with:

```bash
python3 -m pytest
```

Script-level tests should run the actual CLI tools where practical. The shared
test data lives under `tests/test_transcripts/`, and those tests should point
the real scripts at that directory with CLI path arguments instead of relying on
separate test-only codepaths.

## Project Layout

- `src/murder_she_inferred/`: package modules
- `scripts/`: standalone CLI scripts for the current workflow
- `tests/`: unit tests
- `docs/`: user, spec, and roadmap documentation

## Contribution Expectations

- Keep changes aligned with the current project scope in [docs/spec.md](docs/spec.md).
- Update [docs/user-manual.md](docs/user-manual.md) when user-facing workflow,
  commands, configuration, or outputs change.
- Update [docs/roadmap.md](docs/roadmap.md) when a roadmap item is completed,
  reprioritized, or meaningfully redefined.
- Keep script interfaces path-driven so tests can point them at
  `tests/test_transcripts/` and local production/manual use can point them at
  private transcript directories with the same CLI flags.
- Prefer small, reviewable changes that keep the local-first workflow easy to
  understand.
