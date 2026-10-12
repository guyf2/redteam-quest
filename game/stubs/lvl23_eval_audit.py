"""this robustness evaluation was written by a coding agent for a model-security report.
It looks professional. Some of the numbers it prints are wrong. Find out why, from the symptoms."""
import torch
import torch.nn.functional as F


def robust_accuracy(model, x, y, eps):
    """Fraction of images the model still classifies correctly when an attacker may change every pixel by up to eps.
    x: images in [0, 1], shape (N, 1, 28, 28); y: labels; eps: L-infinity budget on the same [0, 1] scale."""
    x, y = x[:32], y[:32]
    x_adv = x.clone().requires_grad_(True)
    F.cross_entropy(model(x_adv), y).backward()
    adv = x + (eps / 255) * x_adv.grad.sign()
    return (model(adv).argmax(1) == y).float().mean().item()
