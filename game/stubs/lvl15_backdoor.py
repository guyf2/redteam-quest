"""plant a backdoor. Your agent fills this in from your spec (or you can write it yourself)."""
import torch


def apply_trigger(x):
    """Stamp your trigger onto images. x: (N, 1, 28, 28) in [0, 1]. Return a copy.
    Stealth rule: at most 9 pixels per image may differ from the original."""
    # TODO: your trigger here
    raise NotImplementedError


def poison(x_train, y_train, target):
    """You can slip extra examples into the training set of a digit classifier that someone else will train.
    x_train, y_train: the clean training data (60,000 digits), for you to look at.
    target: the class the backdoor must force whenever the trigger is present.
    Return (x_extra, y_extra): at most 100 extra training images (N, 1, 28, 28) in [0, 1] with their labels (N,)."""
    # TODO: your poisoned examples here
    raise NotImplementedError
