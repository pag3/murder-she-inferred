# Roadmap

This file is the shared task tracker for the project. It should be updated as
work is completed, reprioritized, or clarified.

## Current Focus

### Stabilize the documented local workflow

- Why it matters: the current pipeline exists, but it is still prototype-grade
  and needs a cleaner path for repeatable use.
- Definition of done: setup, commands, outputs, and expected directories are
  documented and stay in sync with the code.
- Status: in progress

### Improve inference prompt quality

- Why it matters: timeline usefulness depends on timely suspect introductions,
  eliminations, and evidence notes.
- Definition of done: prompt variants can be compared on representative episodes
  and produce clearly better suspect-state updates than the initial baseline.
- Status: in progress

## Next Up

### Define a repeatable QC and evaluation workflow

- Why it matters: the project needs a reliable way to tell whether timeline
  outputs are improving.
- Definition of done: a small reviewed episode set, a clear QC checklist, and a
  repeatable comparison process exist for prompt or model changes.
- Status: planned

### Improve output visualization quality

- Why it matters: the project goal is a chart that makes the narrowing suspect
  field obvious to non-technical viewers.
- Definition of done: chart output is easier to read, highlights state changes
  more clearly, and is suitable for sharing.
- Status: planned

### Clarify timeline output contracts

- Why it matters: downstream QC, plotting, and future model comparison depend on
  stable timeline fields.
- Definition of done: the required structure of timeline JSON and event-level
  fields is documented and reflected consistently across scripts.
- Status: planned

## Later

### Add comparison workflows for prompt profiles and analyzers

- Why it matters: the project should be able to compare multiple inference
  strategies on the same episode inputs.
- Definition of done: outputs from different prompt profiles or analyzers can be
  generated side by side and reviewed consistently.
- Status: later

### Prepare for model-training work

- Why it matters: the future training path will need labeled data and a clear
  replacement point for the current analyzer.
- Definition of done: a labeling format, dataset expectations, and evaluation
  approach are defined before training implementation starts.
- Status: later

## Done

### Establish local data directory configuration

- Why it matters: transcript and output data should live outside the repo when
  needed.
- Definition of done: project-local configuration resolves a default or custom
  data directory without requiring system-wide setup.
- Status: done

### Build transcript chunking pipeline

- Why it matters: the project needs ordered chunks before any temporal inference
  can happen.
- Definition of done: transcript files are ingested, cleaned when needed, and
  chunked into ordered JSON payloads.
- Status: done

### Implement initial Codex CLI timeline inference

- Why it matters: the prototype needs a working chunk-by-chunk analysis pass to
  generate suspect timelines.
- Definition of done: chunk files can be processed into timeline JSON outputs
  using Codex CLI with cumulative context and prior state.
- Status: done

### Add QC and HTML visualization scripts

- Why it matters: generated timelines need lightweight review and a readable
  presentation format.
- Definition of done: timeline JSON can be checked for obvious issues and
  rendered into self-contained HTML charts.
- Status: done

## Open Questions

### What should count as a successful suspect elimination?

- Why it matters: prompt tuning and future evaluation both depend on a shared
  standard for when a suspect is truly out.
- Current note: this needs examples from reviewed episodes, not just prompt wording.

### Which output formats matter most beyond HTML?

- Why it matters: roadmap priorities differ if the main deliverable is for local
  review, publication, or side-by-side analysis.
- Current note: HTML exists today, while PNG and SVG remain aspirational.

