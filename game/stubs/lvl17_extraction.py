"""Level 17: model extraction. Your agent fills this in from your spec (or you can write it yourself)."""
import torch
import torch.nn as nn
import torch.nn.functional as F


def extract(query, pool, budget):
    """Steal a digit classifier through its prediction API.
    query(images) -> class probabilities (N, 10). Every image you pass in counts as one query; you may spend at most `budget`.
    pool: 2,000 unlabelled digit images (N, 1, 28, 28) in [0, 1] that you may choose to send as queries (or invent your own).
    Return a torch module that maps (N, 1, 28, 28) images to (N, 10) logits and agrees with the victim as often as possible."""
    # TODO: your extraction here
    raise NotImplementedError
