"""Level 22: randomized smoothing. Your agent fills this in from your spec (or you can write it yourself)."""
import torch


def radius_from_counts(n_a, n, sigma, alpha):
    """The certified L2 radius, given that the top class won n_a of n noisy votes.
    Use a one-sided (1 - alpha) lower confidence bound on the top-class probability, not the raw fraction.
    Return 0.0 when that lower bound is not above one half (the classifier must abstain)."""
    # TODO: your maths here
    raise NotImplementedError


def certify(model, x, sigma, n0, n, alpha):
    """Certify one image. model: a classifier trained on noisy images; x: one image (1, 1, 28, 28).
    Classify many noisy copies x + N(0, sigma^2): use n0 samples to GUESS the top class, then n FRESH samples
    to estimate it. Return (predicted_class, radius), or (-1, 0.0) to abstain."""
    # TODO: your certification here
    raise NotImplementedError
