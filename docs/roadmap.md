# Roadmap

Categorized to-do list. Each theme is lettered, items numbered.

## A — Local Workflow and Tooling

- [x] A1: Establish local data directory configuration
- [x] A2: Stabilize the documented local workflow (user manual, CONTRIBUTING, README, CLI)
- [x] A3: Set up GitHub Actions CI (pytest on push/PR, Python 3.10 + 3.13)
- [ ] A4: Decide on dependency management (editable install vs PYTHONPATH)

## B — Inference Quality

- [x] B1: Implement Codex CLI timeline inference with cumulative context
- [x] B2: Add scene-mode, paragraph-mode, line-mode, and fixed-size chunking with runt merging
- [x] B3: Add sliding window for transcript context (--context-window)
- [x] B4: Add per-suspect suspicion scores (0-100) to inference output
- [ ] B5: Define what counts as a strong elimination (reviewed transcript examples)
- [ ] B6: Add comparison workflows for alternate analyzers / prompts (enabled by record/replay F6 + provenance E4)

## C — Evaluation and QC

- [x] C1: Add QC script with error rate, empty event, and state consistency checks
- [ ] C2: (Deferred — needs manually-validated episodes; none available yet) Define a repeatable QC workflow with reviewed gold-standard episodes
- [ ] C3: Build a comparison process for evaluating prompt or model changes (enabled by record/replay F6 + provenance E4)
- [ ] C4: Add interim, ground-truth-free curation signals (reveal cleanliness, suspect thrashing, suspicion dynamism) to help select compelling episodes to share

## D — Visualization and Outputs

- [x] D1: State-based heatmap timeline
- [x] D2: Evidence impact ladder
- [x] D3: Elimination bracket / survival board
- [x] D4: Suspicion race chart (line chart of scores over chunks)
- [x] D5: Reveal / climax treatment on heatmap and evidence ladder
- [x] D6: Index page linking all episode views
- [ ] D7: Ranked top-suspect cards (leaderboard snapshots at key moments)
- [ ] D8: Improve output visualization quality and shareability
- [ ] D9: Decide on output formats beyond HTML (PNG, SVG, etc.)

## E — Data Contracts

- [x] E1: Build transcript chunking pipeline
- [x] E2: Implement initial timeline inference
- [ ] E3: Document the timeline JSON schema formally
- [ ] E4: Embed run provenance (model, backend, prompt version/hash, params, timestamp) into timeline JSON and surface it on the HTML
- [ ] E5: Define the format for future manually-validated episode labels (per-chunk suspect states + final verdict), mirroring the timeline JSON — a forward-looking contract with no instances yet (see G1)

## F — Local Model Inference

Add a local-model backend as an alternative to Codex CLI. Codex CLI remains
the primary path (uses chat subscription, no API credits). The local backend
targets any OpenAI-compatible server (Ollama, llama.cpp, LM Studio, OpenVINO)
so the same code works across Mac (Metal GPU) and Windows (CUDA, and eventually
NPU via OpenVINO/Vulkan).

- [x] F1: Refactor inference to separate prompt/parsing logic from the Codex CLI transport
- [x] F2: Add local-model backend that calls an OpenAI-compatible chat completions endpoint
- [x] F3: Add --backend flag (codex-cli | local) and --api-url / --model config
- [x] F4: Document recommended local setups per platform (Mac/Ollama, Windows/CUDA, Windows/NPU)
- [x] F5: Add unit/integration tests for the Codex CLI and local HTTP backends
- [ ] F6: Add record/replay backend — capture live LLM responses during inference and replay them offline for deterministic re-rendering, cheap visualization iteration, and reproducible shareable artifacts

## G — Future Training Work

Gated on a manually-validated dataset of suspect progression that does not exist
yet and cannot be sourced today. Parked until such labels become available. The
record/replay (F6) and provenance (E4) work is the substrate that will let past
runs be scored retroactively once labels exist.

- [ ] G1: Define labeling format, dataset expectations, and evaluation approach (see E5)
