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

#### Clarify which visualizations are possible now versus which need richer data

- Status: planned
- Why it matters: the current timeline outputs already support several strong
  state-based visuals, but score-driven charts will need a deliberate timeline
  data contract extension rather than just front-end polish.
- Definition of done: the roadmap and future visualization work clearly
  distinguish charts that can be built from current fields such as
  `introduced`, `eliminated`, `evidence`,
  `active_suspects_after_chunk`, and `eliminated_suspects_after_chunk`
  from charts that require per-chunk suspicion scores.

#### Improve output visualization quality

- Status: planned
- Why it matters: the project goal is a chart that makes the narrowing suspect
  field obvious to non-technical viewers.
- Definition of done: chart output is easier to read, highlights state changes
  more clearly, and is suitable for sharing.

#### Build a state-based heatmap timeline from current outputs

- Status: planned
- Why it matters: the existing timeline JSON already supports a clearer visual
  overview than the current chart by showing suspect introduction, persistence,
  and elimination in one scan-friendly grid.
- Definition of done: a heatmap-style chart renders current suspect states using
  the existing categorical output only, with distinct treatments for
  not-yet-introduced, active, and eliminated suspects.

#### Build an elimination bracket or survival board from current outputs

- Status: planned
- Why it matters: a survival-style infographic is a strong social-friendly way
  to show who stays in contention and when each suspect drops out.
- Definition of done: an episode output can render suspects as a progressive
  field that narrows over time using existing introduction and elimination
  events without needing numeric suspicion values.

#### Build an evidence impact ladder from current outputs

- Status: planned
- Why it matters: the project already captures implicating and clearing notes,
  which can be repackaged into a compact clue-driven story for each episode.
- Definition of done: an episode output highlights the most important evidence
  beats in order using existing `evidence` annotations and ties them back to
  the relevant suspect and chunk.

#### Decide which output formats matter beyond HTML

- Status: planned
- Why it matters: visualization priorities differ depending on whether the main
  deliverable is local review, publication, or side-by-side analysis.
- Definition of done: the project explicitly prioritizes HTML-only for now or
  names the next export format to support after HTML.

### Later

#### Add per-chunk suspicion scores as an optional timeline extension

- Status: later
- Why it matters: some of the strongest infographic concepts need more than
  categorical suspect state and evidence notes; they need a numeric suspicion
  score tracked for each suspect across chunks.
- Definition of done: the timeline contract can optionally carry per-chunk
  suspicion scores per suspect while preserving the existing active/eliminated
  model for current visualizations and QC.

#### Build a suspicion race chart once score data exists

- Status: later
- Why it matters: a race-style line chart is one of the clearest ways to show
  suspicion rising and falling across an episode, but it depends on chunk-level
  score movement rather than binary state changes.
- Definition of done: an episode output can plot each suspect's suspicion score
  over time using the future per-chunk score map rather than inferring rank from
  categorical state alone.

#### Build ranked top-suspect cards once score data exists

- Status: later
- Why it matters: ranked act-by-act cards are compelling for social sharing, but
  numeric ordering cannot be derived reliably from the current active/eliminated
  model.
- Definition of done: episode outputs can render ranked suspect snapshots for
  key points in the story using score-derived ordering rather than implying
  precision from evidence notes alone.

#### Build a score-intensity heatmap timeline once score data exists

- Status: later
- Why it matters: a richer heatmap with color intensity would communicate not
  just whether a suspect is still in play, but how strongly the model suspects
  them at each point.
- Definition of done: a second heatmap mode renders per-suspect suspicion score
  intensity by chunk, distinct from the state-based heatmap supported by the
  current timeline JSON.

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
