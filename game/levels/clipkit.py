"""CLIP zero-shot classifier on CIFAR-10 for the multimodal levels (loaded lazily, cached per process)."""
import io
from functools import lru_cache

import numpy as np
import torch
from PIL import Image

from . import llm
from .common import DATA, DEV

MODEL = "openai/clip-vit-base-patch32"
NAMES = ["airplane", "automobile", "bird", "cat", "deer", "dog", "frog", "horse", "ship", "truck"]


@lru_cache(maxsize=1)
def _load():
    import logging
    import os
    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
    logging.getLogger("transformers").setLevel(logging.ERROR)
    from torchvision import datasets
    from transformers import CLIPModel, CLIPProcessor
    llm.free_gpu()  # the language models and CLIP do not both fit comfortably in 12 GB
    model = CLIPModel.from_pretrained(MODEL).to(DEV).eval()
    for p in model.parameters():
        p.requires_grad_(False)
    proc = CLIPProcessor.from_pretrained(MODEL)
    tin = proc(text=[f"a photo of a {c}" for c in NAMES], return_tensors="pt", padding=True).to(DEV)
    mean = torch.tensor(proc.image_processor.image_mean, device=DEV).view(1, 3, 1, 1)
    std = torch.tensor(proc.image_processor.image_std, device=DEV).view(1, 3, 1, 1)
    ds = datasets.CIFAR10(DATA, train=False, download=True)
    return model, tin, mean, std, ds


def logits(x):
    """x: (N, 3, 224, 224) floats in [0, 1] -> (N, 10) zero-shot class logits. Differentiable."""
    model, tin, mean, std, _ = _load()
    return model(input_ids=tin["input_ids"], attention_mask=tin["attention_mask"], pixel_values=(x - mean) / std).logits_per_image


def pil_to_tensor(im):
    return torch.from_numpy(np.array(im.convert("RGB").resize((224, 224), Image.BICUBIC))).permute(2, 0, 1).float().div(255)


def tensor_to_pil(t):
    return Image.fromarray((t.permute(1, 2, 0).cpu().numpy() * 255).round().astype("uint8"))


def samples(n, start=0):
    """n CIFAR-10 test images as PIL (32x32 upscaled to 224) that CLIP classifies correctly, with labels."""
    _, _, _, _, ds = _load()
    out, i = [], start
    while len(out) < n:
        im, y = ds[i]
        im224 = im.resize((224, 224), Image.BICUBIC)
        with torch.no_grad():
            ok = logits(pil_to_tensor(im224).unsqueeze(0).to(DEV)).argmax(1).item() == y
        if ok:
            out.append((im224, y))
        i += 1
    return out


def jpeg(x, q):
    out = []
    for im in x.cpu():
        b = io.BytesIO()
        tensor_to_pil(im).save(b, "JPEG", quality=q)
        out.append(pil_to_tensor(Image.open(io.BytesIO(b.getvalue()))))
    return torch.stack(out).to(x.device)
