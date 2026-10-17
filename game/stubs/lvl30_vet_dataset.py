"""BOSS: vet a vendor's dataset. Your agent fills this in from your spec (or you can write it yourself)."""
import torch


def vet(x, y, x_trusted, y_trusted):
    """A vendor sent 20,000 labelled digit images to train your company's classifier. You suspect some were tampered with.
    x: (20000, 1, 28, 28) in [0, 1]; y: labels (20000,).
    x_trusted, y_trusted: 1,000 digits from an internal, verified source you can rely on.
    Return a boolean tensor (20000,): True = keep this example, False = discard it."""
    # TODO: your data vetting here
    raise NotImplementedError
