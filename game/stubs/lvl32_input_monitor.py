"""Level 32 (boss): build the input monitor. Your agent fills this in from your spec (or you can write it yourself)."""
import torch


def detect(model, x, x_calib):
    """Your company's digit classifier faces adversarial inputs in production. Build the monitor that flags them
    BEFORE the answer is used. model: the deployed classifier (call model(x) for logits). x: a batch of incoming images
    (N, 1, 28, 28) in [0, 1]. x_calib: 1,000 ordinary, clean images from the same source, for calibrating your thresholds.
    Return a boolean tensor (N,): True = suspicious (block), False = looks fine. You do not know the attacker's method or budget."""
    # TODO: your monitor here
    raise NotImplementedError
