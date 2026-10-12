#!/usr/bin/env python3
"""
Smoke test for local ML security lab.
Tests:
1. PyTorch CUDA availability
2. Local LLM via ollama OpenAI-compatible API
3. Local VLM via ollama OpenAI-compatible API
"""

import torch
from openai import OpenAI
import base64
from pathlib import Path
import numpy as np
from PIL import Image
import io


def test_cuda():
    """Verify CUDA is available and working."""
    print("=" * 60)
    print("CUDA Verification")
    print("=" * 60)
    assert torch.cuda.is_available(), "CUDA not available!"
    print(f"✓ PyTorch version: {torch.__version__}")
    print(f"✓ CUDA available: True")
    print(f"✓ GPU device: {torch.cuda.get_device_name(0)}")
    print(f"✓ CUDA capability: {torch.cuda.get_device_capability(0)}")

    # Quick GPU test
    a = torch.randn(100, 100, device='cuda')
    b = torch.randn(100, 100, device='cuda')
    c = torch.matmul(a, b)
    print(f"✓ GPU matmul test passed (result shape: {c.shape})")
    print()


def create_test_image():
    """Create a simple test image (red square with blue border)."""
    img_array = np.zeros((256, 256, 3), dtype=np.uint8)
    # Red center
    img_array[50:200, 50:200] = [255, 0, 0]
    # Blue border
    img_array[40:210, 40:50] = [0, 0, 255]
    img_array[40:210, 200:210] = [0, 0, 255]
    img_array[40:50, 40:210] = [0, 0, 255]
    img_array[200:210, 40:210] = [0, 0, 255]
    # White text area (top)
    img_array[10:35, 50:200] = [255, 255, 255]

    img = Image.fromarray(img_array)
    return img


def image_to_base64(img):
    """Convert PIL Image to base64 string for API."""
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    return img_base64


def test_llm():
    """Test local LLM via ollama OpenAI-compatible API."""
    print("=" * 60)
    print("Local LLM Test (aya-expanse:8b via ollama)")
    print("=" * 60)

    client = OpenAI(
        base_url="http://localhost:11434/v1",
        api_key="ollama"  # dummy key for local ollama
    )

    try:
        response = client.chat.completions.create(
            model="aya-expanse:8b",
            messages=[
                {
                    "role": "user",
                    "content": "What is adversarial robustness in machine learning? Answer in 1-2 sentences."
                }
            ],
            temperature=0.7,
            max_tokens=100,
        )

        reply = response.choices[0].message.content
        print(f"Query: What is adversarial robustness in machine learning?")
        print(f"Model: aya-expanse:8b")
        print(f"Reply:\n{reply}")
        print(f"✓ LLM test passed\n")
        return True
    except Exception as e:
        print(f"✗ LLM test failed: {e}\n")
        return False


def test_vlm():
    """Test local VLM via ollama OpenAI-compatible API."""
    print("=" * 60)
    print("Local VLM Test (llava:7b via ollama)")
    print("=" * 60)

    # Create a test image
    img = create_test_image()
    img_base64 = image_to_base64(img)

    client = OpenAI(
        base_url="http://localhost:11434/v1",
        api_key="ollama"  # dummy key for local ollama
    )

    try:
        response = client.chat.completions.create(
            model="llava:7b",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Describe this image in one sentence."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{img_base64}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.7,
            max_tokens=100,
        )

        reply = response.choices[0].message.content
        print(f"Query: Describe this image in one sentence.")
        print(f"Model: llava:7b")
        print(f"Image: 256x256 test image (red square with blue border)")
        print(f"Reply:\n{reply}")
        print(f"✓ VLM test passed\n")
        return True
    except Exception as e:
        print(f"✗ VLM test failed: {e}\n")
        return False


def main():
    """Run all smoke tests."""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 15 + "ML Security Lab Smoke Test" + " " * 17 + "║")
    print("╚" + "═" * 58 + "╝")
    print("\n")

    test_cuda()

    llm_ok = test_llm()
    vlm_ok = test_vlm()

    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"✓ CUDA: OK")
    print(f"{'✓' if llm_ok else '✗'} LLM (ollama OpenAI API): {'OK' if llm_ok else 'FAILED'}")
    print(f"{'✓' if vlm_ok else '✗'} VLM (ollama OpenAI API): {'OK' if vlm_ok else 'FAILED'}")

    if llm_ok and vlm_ok:
        print("\n✓ All smoke tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed - check ollama is running on http://localhost:11434")
        return 1


if __name__ == "__main__":
    exit(main())
