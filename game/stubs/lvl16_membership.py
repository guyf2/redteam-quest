"""Level 16: membership inference. Your agent fills this in from your spec (or you can write it yourself)."""
import torch
import torch.nn.functional as F


def membership_score(model, x, y, x_aux, y_aux):
    """Was this image part of the model's training set?
    model: the victim, a CIFAR-10 classifier (you can call it, you can see its outputs).
    x: images (N, 3, 32, 32) in [0, 1], y: their true labels (N,). Some were used to train the model, some were not.
    x_aux, y_aux: extra labelled images from the same distribution that the model never saw, for calibration.
    Return a tensor of N scores: HIGHER means 'more likely a training member'."""
    # TODO: your attack here
    raise NotImplementedError
