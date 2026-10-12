"""Textbook reference attacks, used ONLY to draw the visualizations (never to grade the player)."""
import torch
import torch.nn.functional as F


def fgsm(model, x, y, eps):
    xa = x.clone().requires_grad_(True)
    F.cross_entropy(model(xa), y).backward()
    return (x + eps * xa.grad.sign()).clamp(0, 1).detach()


def pgd(model, x, y, eps, steps=20):
    alpha = 2.5 * eps / steps
    xa = (x + torch.empty_like(x).uniform_(-eps, eps)).clamp(0, 1)
    for _ in range(steps):
        xa.requires_grad_(True)
        g = torch.autograd.grad(F.cross_entropy(model(xa), y), xa)[0]
        xa = torch.min(torch.max(xa.detach() + alpha * g.sign(), x - eps), x + eps).clamp(0, 1)
    return xa.detach()


def targeted_pgd(model, x, t, eps, steps=40):
    """Descend the loss toward target class t (instead of ascending the loss of the true class)."""
    alpha = 2.5 * eps / steps
    xa = x.clone()
    for _ in range(steps):
        xa.requires_grad_(True)
        g = torch.autograd.grad(F.cross_entropy(model(xa), t), xa)[0]
        xa = torch.min(torch.max(xa.detach() - alpha * g.sign(), x - eps), x + eps).clamp(0, 1)
    return xa.detach()


def mifgsm(model, x, y, eps, steps=10, mu=1.0):
    """Momentum iterative FGSM: accumulating gradient direction avoids overfitting to one model, so it transfers better."""
    alpha, g, xa = eps / steps, torch.zeros_like(x), x.clone()
    for _ in range(steps):
        xa.requires_grad_(True)
        grad = torch.autograd.grad(F.cross_entropy(model(xa), y), xa)[0]
        g = mu * g + grad / grad.abs().mean(dim=(1, 2, 3), keepdim=True).clamp_min(1e-12)
        xa = torch.min(torch.max(xa.detach() + alpha * g.sign(), x - eps), x + eps).clamp(0, 1)
    return xa.detach()


def bpda_pgd(model, base, quant, x, y, eps, steps=40):
    """BPDA: forward through the real defended model, but backpropagate as if the non-differentiable step were identity."""
    alpha, xa = 2.5 * eps / steps, x.clone()
    for _ in range(steps):
        xa.requires_grad_(True)
        xq = xa + (quant(xa) - xa).detach()  # straight-through estimator
        g = torch.autograd.grad(F.cross_entropy(base(xq), y), xa)[0]
        xa = torch.min(torch.max(xa.detach() + alpha * g.sign(), x - eps), x + eps).clamp(0, 1)
    return xa.detach()


def simba(query, x, y, eps, iters=200, seed=0):
    """Score-based black-box attack (SimBA-style): try +/-eps on one random pixel at a time, keep it if the true-class
    probability drops. `query(batch)` returns class probabilities and is the ONLY access to the model."""
    g = torch.Generator(device=x.device).manual_seed(seed)
    xa, n = x.clone(), len(x)
    p = query(xa)[torch.arange(n), y]
    for _ in range(iters):
        idx = torch.randint(0, x[0].numel(), (n,), device=x.device, generator=g)
        for sign in (1.0, -1.0):
            cand = xa.clone().view(n, -1)
            cand[torch.arange(n), idx] = (cand[torch.arange(n), idx] + sign * eps).clamp(0, 1)
            cand = torch.min(torch.max(cand.view_as(x), x - eps), x + eps)
            pc = query(cand)[torch.arange(n), y]
            better = pc < p
            xa[better], p[better] = cand[better], pc[better]
    return xa


def apply_patch(x, patch, locs):
    """Paste patch (1, s, s) into each image of x at the top-left corners in locs."""
    out, s = x.clone(), patch.shape[-1]
    for k, (r, c) in enumerate(locs):
        out[k, :, r:r + s, c:c + s] = patch
    return out


def random_locs(n, size, seed=0):
    g = torch.Generator().manual_seed(seed)
    return [tuple(torch.randint(0, 28 - size + 1, (2,), generator=g).tolist()) for _ in range(n)]


def train_patch(model, X, Y, target, size=8, steps=300, seed=0):
    torch.manual_seed(seed)
    w = torch.zeros(1, size, size, device=X.device).uniform_(-1, 1).requires_grad_(True)
    opt = torch.optim.Adam([w], 0.1)
    keep = Y != target
    Xk = X[keep]
    for _ in range(steps):
        i = torch.randint(0, len(Xk), (128,), device=X.device)
        r, c = torch.randint(0, 28 - size + 1, (2,)).tolist()
        xb = Xk[i].clone()
        xb[:, :, r:r + size, c:c + size] = torch.sigmoid(w)
        loss = F.cross_entropy(model(xb), torch.full((128,), target, device=X.device))
        opt.zero_grad()
        loss.backward()
        opt.step()
    return torch.sigmoid(w).detach()
