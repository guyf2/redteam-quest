"""Level 13: adversarial image against CLIP. Your agent fills this in from your spec (or you can write it yourself)."""
import torch
import torch.nn.functional as F


def attack_clip(logits_fn, x, target, eps):
    """logits_fn(images) -> (N, 10) zero-shot class logits of CLIP; differentiable.
    x: images in [0, 1], shape (N, 3, 224, 224); target: the class each image must be read as, shape (N,).
    Return adversarial images (same shape, each pixel within eps of x, inside [0, 1]).
    WARNING: the real service shrinks and recompresses every image before CLIP sees it. You are not told the details."""
    # TODO: your attack here
    raise NotImplementedError
