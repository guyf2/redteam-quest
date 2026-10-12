"""Level 6: adversarial patch. Your agent fills this in from your spec (or you can write it yourself)."""
import torch
import torch.nn.functional as F

PATCH = 14  # the sticker is PATCH x PATCH pixels on a 28 x 28 image


def make_patch(model, x_train, y_train, target):
    """Design ONE sticker that, pasted anywhere on ANY digit, makes the model say `target`.
    x_train: training images in [0, 1], shape (N, 1, 28, 28); y_train: their labels.
    Return a tensor of shape (1, PATCH, PATCH) with values in [0, 1].
    The grader pastes it at random positions on unseen digits (you do not choose the position)."""
    # TODO: your sticker here
    raise NotImplementedError
