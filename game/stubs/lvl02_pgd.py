"""this PGD attack was written by a coding agent. It looks professional. It is broken.
Find the bugs yourself, or tell your agent which symptom to investigate."""
import torch
import torch.nn.functional as F


def pgd(model, x, y, eps, alpha=0.02, steps=20):
    """Projected Gradient Descent attack (Madry et al., 2018), L-inf threat model.

    Starts from a random point in the eps-ball, then takes `steps` signed-gradient steps of size
    `alpha`, projecting back onto the eps-ball and the valid image range after every step.
    Returns adversarial images that maximise the model's loss.
    """
    x_adv = x.clone().detach()
    x_adv = x_adv + torch.empty_like(x_adv).uniform_(-eps, eps)  # random start inside the ball

    for _ in range(steps):
        x_adv.requires_grad_(True)
        loss = F.cross_entropy(model(x_adv), y)
        grad = torch.autograd.grad(loss, x_adv)[0]
        x_adv = x_adv.detach() - alpha * grad.sign()  # ascend the loss

    return x_adv.detach()
