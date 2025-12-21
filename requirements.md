# Murder, She Inferred — Requirements (Minimal)

## Objective
Create **clear, shareable visualizations** that show:
- Who the suspects are at any point in a *Murder, She Wrote* episode
- When suspects are added or eliminated
- How evidence shifts suspicion over time

The focus is *temporal structure*, not perfect probabilities.

---

## Core Output
For each episode, produce:
1. A **timeline** of the episode
2. A **set of suspects active at each point** in that timeline
3. A **visual chart** showing suspects appearing, persisting, and being eliminated

Optionally: annotate moments where evidence strongly implicates or clears someone.

---

## Scope

### In Scope
- Episode transcripts (text only)
- Sequential processing (scene- or line-level)
- Tracking:
  - Suspect introduced
  - Suspect still viable
  - Suspect eliminated
- Simple evidence notes ("implicating", "exonerating", "misleading")
- Visualizations suitable for sharing (PNG, SVG, interactive HTML)

### Out of Scope (for now)
- Accurate probability modeling
- Video/audio cues
- Psychological realism
- Real-time inference

---

## Data Requirements
- Plain-text transcripts
- Episode metadata (season, episode, title, year)
- Strict preservation of transcript order

---

## Functional Requirements

### FR-1: Transcript Ingestion
- Load transcript from local file
- Preserve original order
- Split into sequential units (chunks: lines, beats, or scenes)

### FR-2: LLM-Based Chunk Analysis
- Process the transcript **chunk by chunk** using an LLM
- For each chunk, extract:
  - Newly introduced characters
  - Characters who become plausible suspects
  - Characters who are explicitly or implicitly cleared
- The LLM must only see the current and prior chunks (no future leakage)

### FR-3: Suspect State Tracking
- Maintain a running set of suspects with simple states:
  - active
  - eliminated
- Update suspect states incrementally based on LLM output

### FR-4: Evidence Annotation (Lightweight)
- Attach short, human-readable notes to chunk boundaries:
  - implicates X
  - clears X
  - misleading / red herring

No numeric scoring required.

### FR-5: Visualization
- X-axis: episode progression (chunk index or time)
- Y-axis: suspects
- Visual state:
  - active
  - eliminated
  - newly introduced

The viewer should be able to see *at a glance* how the suspect field narrows.

---

## Non-Functional Requirements
- Runs locally
- Deterministic and reproducible
- Simple enough to understand by reading the code

---

## Success Criteria
The project succeeds if:
- Each episode produces a clean, readable suspect timeline
- The narrowing of suspects over time is visually obvious
- A non-technical viewer can understand the chart without explanation

---

## Model Training & Fine-Tuning (Planned Extension)

This project may be extended to include **model training** focused on learning how *suspect states evolve over time* in a mystery narrative.

The goal of training is **not** to predict the murderer, but to learn structured, incremental updates to the suspect set based on newly revealed information.

---

## Training Objective

Train a model to map:

> *(current transcript chunk + current suspect set)* → *suspect state changes*

Supported state changes:
- introduce suspect
- maintain suspect
- eliminate suspect

Optional annotations:
- evidence implicating suspect
- evidence exonerating suspect
- red herring

This is a **multi-label, per-chunk classification problem**.

---

## Training Data

### Labeled Examples
Each training example consists of:
- Episode ID
- Chunk index
- Chunk text
- Active suspects before the chunk
- One or more labeled state changes

Labels may be created by:
- Manual annotation of a small episode subset
- LLM-assisted bootstrapping followed by human correction

---

## Model Constraints
- The model must not have access to future chunks
- The model must operate incrementally
- Deterministic inference modes must be supported

---

## Integration with Visualization

The trained model must be usable as a drop-in replacement for the LLM-based chunk analyzer, producing the same suspect timeline outputs so that:
- LLM-based inference
- trained-model inference
- human annotations

can be visually compared on identical plots.

---

## Evaluation

Model quality is assessed by demonstrating:
- Correct timing of suspect elimination
- Reduction of implausible suspects over time
- Alignment with human-labeled timelines

Accuracy of final murderer prediction is **explicitly not a metric**.

---

## Future (Explicitly Optional)
- Probability scoring
- Cross-episode generalization
- Cross-series evaluation
- Automated label refinement

