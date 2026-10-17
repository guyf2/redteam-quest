"""adversarial training. Your agent fills this in from your spec (or you can write it yourself)."""
import torch
import torch.nn.functional as F


def train_robust(model, x_train, y_train, eps):
    """Train `model` (a fresh digit classifier) so that it stays accurate under attack.
    x_train: images in [0, 1], shape (60000, 1, 28, 28); y_train: labels.
    eps: the L-infinity attack budget the model must withstand.
    Keep training under about a minute. Return the trained model."""
    # TODO: your training loop here
    raise NotImplementedError
