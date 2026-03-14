# Project Spec

## Objective

Create clear, shareable visualizations that show:
- who the suspects are at any point in a *Murder, She Wrote* episode
- when suspects are added or eliminated
- how evidence shifts suspicion over time

The focus is temporal structure, not perfect probabilities.

## Core Outputs

For each episode, the project should produce:
1. A timeline of the episode
2. A set of suspects active at each point in that timeline
3. A visual chart showing suspects appearing, persisting, and being eliminated

Optionally, the output may annotate moments where evidence strongly implicates
or clears someone.

## Scope

### In Scope

- plain-text episode transcripts
- sequential processing of transcript chunks
- tracking suspect introduction, persistence, and elimination
- lightweight evidence notes such as implicating and clearing events
- shareable visual outputs such as HTML, PNG, or SVG

### Out of Scope

- accurate probability modeling
- video or audio cues
- psychological realism
- real-time inference

## Functional Requirements

### Transcript Ingestion

- Load transcripts from local files
- Preserve transcript order
- Split transcripts into sequential units such as scenes, paragraphs, lines, or fixed chunks

### Chunk Analysis

- Process transcripts chunk by chunk using an LLM or equivalent analyzer
- Extract:
  - newly introduced characters
  - characters who become plausible suspects
  - characters who are explicitly or implicitly cleared
- Prevent future leakage by limiting each step to the current and prior transcript content

### Suspect State Tracking

- Maintain a running set of suspects with simple states
- Support at least:
  - `active`
  - `eliminated`
- Update state incrementally from chunk-level analysis outputs

### Evidence Annotation

- Attach short, human-readable evidence notes to chunk boundaries
- Support at least:
  - implicates suspect
  - clears suspect

### Visualization

- Represent episode progression on the x-axis
- Represent suspects on the y-axis
- Make suspect state changes readable at a glance

## Non-Functional Requirements

- Run locally
- Be deterministic and reproducible where possible
- Stay simple enough that a contributor can understand the codebase without heavy framework knowledge

## Success Criteria

The project succeeds if:
- each episode produces a clean, readable suspect timeline
- the narrowing of suspects over time is visually obvious
- a non-technical viewer can understand the chart without explanation

## Future Extension: Model Training

The project may later grow a training and evaluation path focused on learning
how suspect states evolve over time in a mystery narrative.

The goal of that future work is not to predict the murderer directly. It is to
learn structured, incremental updates to the suspect set from new transcript
chunks.

If implemented later, the trained model should act as a drop-in replacement for
the current chunk analyzer so LLM-based inference, trained-model inference, and
human annotations can be compared on the same outputs.

