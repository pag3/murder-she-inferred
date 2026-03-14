# Roadmap

This file is the shared task tracker for the project. It is organized by
capability area so current work, planned work, and completed work are easier to
scan and maintain.

## Local Workflow and Tooling

Keep the local-first workflow reliable, documented, and easy to repeat.

### Current

#### Stabilize the documented local workflow

- Status: in progress
- Why it matters: the prototype is usable, but it still needs a dependable path
  from setup through outputs.
- Definition of done: setup, commands, directory expectations, and generated
  artifacts stay in sync with the code and are easy for a new contributor to follow.

### Next

#### Keep automated test checks lightweight and reliable

- Status: planned
- Why it matters: low-friction CI is the fastest way to catch regressions in
  the package code.
- Definition of done: GitHub Actions runs the unit test suite on pushes to
  `main` and on pull requests, and contributors treat `python -m pytest` as the
  default pre-PR check.

### Done

#### Establish local data directory configuration

- Status: done
- Why it matters: transcript and output data should live outside the repo when
  needed.
- Definition of done: project-local configuration resolves a default or custom
  data directory without requiring system-wide setup.

## Inference Quality

Improve the quality of suspect introductions, eliminations, and evidence notes
produced by the analyzer.

### Current

#### Improve inference prompt quality

- Status: in progress
- Why it matters: timeline usefulness depends on whether suspect-state updates
  happen at the right moments and with the right confidence.
- Definition of done: the default prompt produces clearer suspect
  introductions, eliminations, and evidence notes on representative episodes.

### Next

#### Define what counts as a strong elimination

- Status: planned
- Why it matters: prompt tuning needs a shared standard for when a suspect is
  genuinely out versus just temporarily less likely.
- Definition of done: reviewed transcript examples establish when eliminations
  should happen and those examples guide prompt iteration.

### Later

#### Add comparison workflows for analyzers

- Status: later
- Why it matters: the project should be able to compare multiple inference
  strategies on the same episode inputs.
- Definition of done: outputs from alternate prompts or future analyzers can be
  generated side by side and reviewed consistently.

## Evaluation and QC

Make output quality measurable enough that changes can be judged on more than
intuition.

### Next

#### Define a repeatable QC and evaluation workflow

- Status: planned
- Why it matters: the project needs a reliable way to tell whether timeline
  outputs are improving.
- Definition of done: a small reviewed episode set, a clear QC checklist, and a
  repeatable comparison process exist for prompt or model changes.

## Visualization and Outputs

Make the resulting timelines easier to read and easier to share.

### Next

#### Improve output visualization quality

- Status: planned
- Why it matters: the project goal is a chart that makes the narrowing suspect
  field obvious to non-technical viewers.
- Definition of done: chart output is easier to read, highlights state changes
  more clearly, and is suitable for sharing.

#### Decide which output formats matter beyond HTML

- Status: planned
- Why it matters: visualization priorities differ depending on whether the main
  deliverable is local review, publication, or side-by-side analysis.
- Definition of done: the project explicitly prioritizes HTML-only for now or
  names the next export format to support after HTML.

### Done

#### Add QC and HTML visualization scripts

- Status: done
- Why it matters: generated timelines need lightweight review and a readable
  presentation format.
- Definition of done: timeline JSON can be checked for obvious issues and
  rendered into self-contained HTML charts.

## Data Contracts and Comparisons

Keep timeline outputs stable enough that downstream tooling and future
comparisons remain straightforward.

### Next

#### Clarify timeline output contracts

- Status: planned
- Why it matters: QC, plotting, and future analyzer comparisons depend on a
  stable timeline shape.
- Definition of done: the required timeline JSON structure and core event-level
  fields are documented and reflected consistently across scripts.

### Done

#### Build transcript chunking pipeline

- Status: done
- Why it matters: the project needs ordered chunks before any temporal inference
  can happen.
- Definition of done: transcript files are ingested, cleaned when needed, and
  chunked into ordered JSON payloads.

#### Implement initial Codex CLI timeline inference

- Status: done
- Why it matters: the prototype needs a working chunk-by-chunk analysis pass to
  generate suspect timelines.
- Definition of done: chunk files can be processed into timeline JSON outputs
  using Codex CLI with cumulative context and prior state.

## Future Training Work

Reserve space for model-training work without letting it dominate current
prototype priorities.

### Later

#### Prepare for model-training work

- Status: later
- Why it matters: the future training path will need labeled data and a clear
  replacement point for the current analyzer.
- Definition of done: a labeling format, dataset expectations, and evaluation
  approach are defined before training implementation starts.
