# Lab 00: ML Security Lab Setup

Local environment for ML security research and adversarial testing. Includes PyTorch with CUDA support, ML security tools, and local LLM/VLM inference via ollama.

## Hardware

- **GPU**: NVIDIA GeForce RTX 5070 Ti Laptop (Blackwell, sm_120, 12GB VRAM)
- **Python**: 3.12.3
- **CUDA**: 12.1 (via PyTorch cu121/cu130 wheels)

## Environment Setup

### Create Virtual Environment

```bash
cd labs/00-setup
python3.12 -m venv .venv
source .venv/bin/activate
```

### Install Dependencies

```bash
# PyTorch with CUDA (using PyTorch index for Blackwell support)
uv pip install --index https://download.pytorch.org/whl/cu121 torch torchvision

# ML and Security Tools
uv pip install transformers accelerate bitsandbytes
uv pip install torchattacks adversarial-robustness-toolbox
uv pip install garak pyrit inspect-ai openai
uv pip install pillow matplotlib scipy scikit-learn
```

## Installed Versions

```
PyTorch: 2.14.1+cu130
TorchVision: 0.29.1+cu130
Transformers: 5.18.0
Accelerate: 1.2.0
Bitsandbytes: 0.41.3
Garak: 0.17.0
PyRIT: 1.1.0
TorchAttacks: 3.5.1
Adversarial-Robustness-Toolbox: 1.20.1
Inspect-AI: 0.4.0
OpenAI (client): 1.59.4
```

## Local Models (Ollama)

### Instruct LLM

- **Name**: `aya-expanse:8b`
- **Size**: 5.1 GB
- **Type**: Instruct model (Cohere multilingual)

### Vision-Language Model

- **Name**: `llava:7b`
- **Size**: 4.7 GB
- **Type**: Vision-language model for image understanding

Both models are served via ollama's OpenAI-compatible API at `http://localhost:11434/v1`.

### Start Ollama

```bash
ollama serve
```

In another terminal, verify models are available:

```bash
ollama list
```

## Smoke Test

Verify CUDA, LLM, and VLM are working:

```bash
cd labs/00-setup
source .venv/bin/activate
python3 smoke_test.py
```

Expected output:
```
✓ CUDA: OK
✓ LLM (ollama OpenAI API): OK
✓ VLM (ollama OpenAI API): OK
✓ All smoke tests passed!
```

## Security Testing with Garak

Run adversarial probes against the local LLM:

```bash
source .venv/bin/activate
garak --target_type ollama --target_name "aya-expanse:8b" --spec 'probes.dan.DAN_Jailbreak' --generations 1
```

Other available probe categories:
- `probes.dan` - DAN (Do Anything Now) jailbreak variants
- `probes.promptinject` - Prompt injection attacks
- `probes.pii` - Personally Identifiable Information extraction
- `probes.encoding` - Encoding-based attacks

View reports in `~/.local/share/garak/garak_runs/`.

## PyRIT Security Testing

PyRIT (Python Risk Identification Toolkit) for multi-turn LLM security testing:

```python
from pyrit.prompt_target import OpenAIChatTarget
from pyrit.datasets import fetch_cyberattack_conversation

# Configure to use local ollama
target = OpenAIChatTarget(
    endpoint="http://localhost:11434/v1",
    api_key="ollama",
    deployment_name="aya-expanse:8b"
)
```

## Next Steps

This lab provides the foundation for:
1. Adversarial example generation (torchattacks, ART)
2. LLM prompt injection and jailbreak testing (garak, PyRIT)
3. Vision model robustness testing (adversarial images with llava)
4. Red team scenario design and execution

See main course README for phase-specific labs.

## Troubleshooting

### CUDA Not Available
- Verify RTX 5070 Ti is detected: `nvidia-smi`
- Reinstall torch: `pip install --force-reinstall --no-cache-dir torch torchvision`

### Ollama Connection Failed
- Ensure ollama is running: `ollama serve`
- Check endpoint: `curl http://localhost:11434/v1/models`

### Package Installation Failed
- Some packages (bitsandbytes, garak) require specific build tools
- On Linux, may need: `sudo apt-get install build-essential libssl-dev`
- Rerun installation with: `uv pip install --no-build-isolation [package]`

---

**Last verified**: 2026-10-01  
**Python**: 3.12.3  
**PyTorch**: 2.14.1+cu130  
**GPU**: RTX 5070 Ti (Blackwell, CUDA 12.1)
