"""targeted attack. Your agent fills this in from your spec (or you can write it yourself)."""
import torch
import torch.nn.functional as F


def targeted_attack(model, x, target, eps):
    """x: images in [0, 1], shape (N, 1, 28, 28); target: the class you WANT the model to output, shape (N,).
    Return adversarial images: same shape, each pixel within eps of x, inside [0, 1],
    that the model classifies as `target`."""
    # TODO: your attack here
    raise NotImplementedError
