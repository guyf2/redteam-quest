"""Level 4: transfer attack. Your agent fills this in from your spec (or you can write it yourself)."""
import torch
import torch.nn.functional as F


def craft(surrogate, x, y, eps):
    """You can see and differentiate `surrogate`, but the real target (a DIFFERENT, hidden model) is a black box.
    x: images in [0, 1], shape (N, 1, 28, 28); y: true labels.
    Return adversarial images (same shape, within eps of x, inside [0, 1]) crafted on the surrogate
    that also fool the hidden victim."""
    # TODO: your attack here
    raise NotImplementedError
