import pathlib

import torch
import torch.nn as nn
from torchvision import datasets

DATA = pathlib.Path(__file__).resolve().parents[2] / "data"
DEV = "cuda" if torch.cuda.is_available() else "cpu"


class Net(nn.Module):
    def __init__(self):
        super().__init__()
        self.c = nn.Sequential(
            nn.Conv2d(1, 16, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(16, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Flatten(), nn.Linear(32 * 7 * 7, 10))

    def forward(self, x):
        return self.c(x)


def _tensors(train):
    ds = datasets.MNIST(DATA, train=train, download=True)
    return ds.data.float().div(255).unsqueeze(1).to(DEV), ds.targets.to(DEV)


def target():
    """The victim: a small MNIST CNN (trained once, cached) plus 500 test images in [0, 1]."""
    path = DATA / "mnist_cnn.pt"
    model = Net().to(DEV)
    if path.exists():
        model.load_state_dict(torch.load(path, map_location=DEV))
    else:
        print("Training the victim model (one-time, ~20s)...")
        X, Y = _tensors(True)
        opt = torch.optim.Adam(model.parameters(), 1e-3)
        for _ in range(2):
            for i in torch.randperm(len(X), device=DEV).split(128):
                opt.zero_grad()
                nn.functional.cross_entropy(model(X[i]), Y[i]).backward()
                opt.step()
        path.parent.mkdir(exist_ok=True)
        torch.save(model.state_dict(), path)
    model.eval()
    Xt, Yt = _tensors(False)
    return model, Xt[:500], Yt[:500]


def acc(model, x, y):
    with torch.no_grad():
        return (model(x).argmax(1) == y).float().mean().item()


def art(img):
    """28x28 tensor -> 14 text rows."""
    chars = " .:-=+*#%@"
    return ["".join(chars[min(9, int(v * 10))] for v in row) for row in img[0].cpu()[::2]]


class MLP(nn.Module):
    """A differently-shaped victim (no convolutions) for the transferability level."""
    def __init__(self):
        super().__init__()
        self.c = nn.Sequential(nn.Flatten(), nn.Linear(784, 256), nn.ReLU(), nn.Linear(256, 128), nn.ReLU(), nn.Linear(128, 10))

    def forward(self, x):
        return self.c(x)


def fit(model, X, Y, epochs=2, lr=1e-3, seed=0, aug=None):
    torch.manual_seed(seed)
    opt = torch.optim.Adam(model.parameters(), lr)
    for _ in range(epochs):
        for i in torch.randperm(len(X), device=DEV).split(128):
            xb = aug(X[i]) if aug else X[i]
            opt.zero_grad()
            nn.functional.cross_entropy(model(xb), Y[i]).backward()
            opt.step()
    model.eval()
    return model


def cached(name, make, train):
    """Train once, cache the weights in data/, return the model in eval mode."""
    path = DATA / f"{name}.pt"
    model = make().to(DEV)
    if path.exists():
        model.load_state_dict(torch.load(path, map_location=DEV))
        return model.eval()
    X, Y = _tensors(True)
    train(model, X, Y)
    path.parent.mkdir(exist_ok=True)
    torch.save(model.state_dict(), path)
    return model


def victim_b():
    """Black-box victim for the transfer level: an MLP trained with a different seed. Returns model, X, Y."""
    model = cached("mnist_mlp", MLP, lambda m, X, Y: fit(m, X, Y, epochs=3, seed=7))
    Xt, Yt = _tensors(False)
    return model, Xt[:500], Yt[:500]


def quantize(x, levels=4):
    return torch.round(x * (levels - 1)) / (levels - 1)


class Defended(nn.Module):
    """A 'robust' model: snap every pixel to a few grey levels before classifying (input quantization)."""
    def __init__(self, base, levels=4):
        super().__init__()
        self.base, self.levels = base, levels

    def forward(self, x):
        return self.base(quantize(x, self.levels))


class CifarCNN(nn.Module):
    """Small CIFAR-10 classifier for the privacy level (it overfits easily on purpose)."""
    def __init__(self):
        super().__init__()
        self.f = nn.Sequential(nn.Conv2d(3, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2), nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
                               nn.Flatten(), nn.Linear(64 * 8 * 8, 256), nn.ReLU(), nn.Linear(256, 10))

    def forward(self, x):
        return self.f(x)


def cifar(train, n, offset=0):
    """n CIFAR-10 images as (N, 3, 32, 32) floats in [0, 1] plus labels, on the compute device."""
    ds = datasets.CIFAR10(DATA, train=train, download=True)
    X = torch.from_numpy(ds.data[offset:offset + n]).permute(0, 3, 1, 2).float().div(255).to(DEV)
    return X, torch.tensor(ds.targets[offset:offset + n]).to(DEV)


def auc(scores, labels):
    from sklearn.metrics import roc_auc_score
    s = scores.detach().float().cpu().numpy() if torch.is_tensor(scores) else scores
    return float(roc_auc_score(labels.cpu().numpy() if torch.is_tensor(labels) else labels, s))


def noisy_base(sigma=0.25):
    """MNIST classifier trained with Gaussian noise of std sigma (the base model for randomized smoothing)."""
    return cached("mnist_noisy", Net, lambda m, X, Y: fit(m, X, Y, epochs=3, seed=0, aug=lambda x: x + sigma * torch.randn_like(x)))
