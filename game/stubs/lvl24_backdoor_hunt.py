"""Level 24: find the backdoor. Your agent fills this in from your spec (or you can write it yourself)."""
import torch
import torch.nn.functional as F


def find_backdoor(models, x):
    """Exactly one of the three digit classifiers in `models` was trained on poisoned data: a small hidden pattern
    in the image forces it to output one particular class. The other two are clean.
    x: 200 clean test images (200, 1, 28, 28) in [0, 1] you may use.
    You do not know the trigger, its position, or its target class. Return (index_of_backdoored_model, target_class)."""
    # TODO: your forensics here
    raise NotImplementedError
