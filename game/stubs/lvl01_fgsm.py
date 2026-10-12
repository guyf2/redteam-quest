"""Level 1: FGSM. Your agent fills this in from your spec (or you can write it yourself)."""
import torch
import torch.nn.functional as F


def fgsm(model, x, y, eps):
    """x: images in [0, 1], shape (N, 1, 28, 28); y: true labels.
    Return adversarial images: same shape, each pixel within eps of x, clipped to [0, 1]."""
    # TODO: your attack here
    raise NotImplementedError
