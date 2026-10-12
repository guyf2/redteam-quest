"""Level 5: black-box attack. Your agent fills this in from your spec (or you can write it yourself)."""
import torch


def blackbox_attack(query, x, y, eps, queries_per_image):
    """You have NO gradients and NO weights. The only access to the model is `query(images)`, which returns the
    class probabilities, shape (N, 10), and COUNTS every image you pass in as one query.
    x: images in [0, 1], shape (N, 1, 28, 28); y: true labels.
    You may use at most `queries_per_image` queries per image on average (total budget = N * queries_per_image).
    Return adversarial images: same shape, within eps of x, inside [0, 1], that the model misclassifies."""
    # TODO: your attack here
    raise NotImplementedError
