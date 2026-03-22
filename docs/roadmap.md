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
- [ ] B6: Add comparison workflows for alternate analyzers / prompts

## C — Evaluation and QC

- [x] C1: Add QC script with error rate, empty event, and state consistency checks
- [ ] C2: Define a repeatable QC workflow with reviewed gold-standard episodes
- [ ] C3: Build a comparison process for evaluating prompt or model changes

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

## F — Local Model Inference

Add a local-model backend as an alternative to Codex CLI. Codex CLI remains
the primary path (uses chat subscription, no API credits). The local backend
targets any OpenAI-compatible server (Ollama, llama.cpp, LM Studio, OpenVINO)
so the same code works across Mac (Metal GPU) and Windows (CUDA, and eventually
NPU via OpenVINO/Vulkan).

- [ ] F1: Refactor inference to separate prompt/parsing logic from the Codex CLI transport
- [ ] F2: Add local-model backend that calls an OpenAI-compatible chat completions endpoint
- [ ] F3: Add --backend flag (codex-cli | local) and --api-url / --model config
- [ ] F4: Document recommended local setups per platform (Mac/Ollama, Windows/CUDA, Windows/NPU)
- [ ] F5: Test and validate output parity between Codex CLI and local model backends

## G — Future Training Work

- [ ] G1: Define labeling format, dataset expectations, and evaluation approach
