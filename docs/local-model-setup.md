# Local Model Setup

This project can use any OpenAI-compatible server as an alternative to Codex CLI for inference. This doc covers recommended setups per platform.

## Quick Reference

| Platform | GPU | Recommended Backend | Install |
|---|---|---|---|
| macOS | Apple Metal | Ollama | `brew install ollama` |
| Windows | NVIDIA CUDA | Ollama | Download from ollama.com |
| Windows | Intel NPU | OpenVINO Model Server | See Intel docs (experimental) |
| Linux | NVIDIA CUDA | Ollama | `curl -fsSL https://ollama.com/install.sh \| sh` |

## Ollama Quickstart

```bash
ollama pull llama3
ollama serve  # starts on http://localhost:11434
# Verify it's running:
curl http://localhost:11434/v1/chat/completions \
  -d '{"model":"llama3","messages":[{"role":"user","content":"hi"}]}'
```

## Running Inference with a Local Model

```bash
PYTHONPATH=src python scripts/infer_timelines.py \
  --backend local \
  --model llama3 \
  --run-root test-run
```

## Customizing the Endpoint

```bash
# For a non-default server (e.g., llama.cpp on port 8080):
PYTHONPATH=src python scripts/infer_timelines.py \
  --backend local \
  --api-url http://localhost:8080/v1/chat/completions \
  --model my-model \
  --run-root test-run
```

## Notes

- Ollama uses Metal GPU automatically on Mac, CUDA on Windows/Linux with NVIDIA.
- Model quality matters — larger models (13B+) produce better timeline analysis.
- The `--timeout` flag (default 120s) may need increasing for larger models on CPU.
- NPU support via OpenVINO is experimental; see Intel's documentation for current status.
