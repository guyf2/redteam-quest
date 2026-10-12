"""BOSS: break the 'robust' model. Your agent fills this in from your spec (or you can write it yourself)."""
import torch
import torch.nn.functional as F


def break_defense(defended, x, y, eps):
    """`defended` is a model with a published robustness claim. Call defended(x) for logits.
    Under the hood it snaps every pixel to `defended.levels` grey levels, then runs the CNN `defended.base`.
    x: images in [0, 1], shape (N, 1, 28, 28); y: true labels.
    Return adversarial images: same shape, each pixel within eps of x, inside [0, 1],
    that make `defended` misclassify."""
    # TODO: your attack here
    raise NotImplementedError
