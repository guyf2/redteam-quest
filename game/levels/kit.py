"""Helpers shared by level graders."""
import importlib.util

import torch


def call(path, name, *args):
    """Run the player's function `name` from the file at `path`. Returns (value, None) or (None, friendly error)."""
    try:
        spec = importlib.util.spec_from_file_location("student", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if not hasattr(mod, name):
            return None, f"The file must define a function named `{name}`."
        return getattr(mod, name)(*args), None
    except NotImplementedError:
        return None, "The function is still empty (it raises NotImplementedError)."
    except Exception as e:  # player code can fail in any way; show it
        return None, f"The code crashed: {type(e).__name__}: {e}"


def check_images(adv, x, eps, what="pixel"):
    """Enforce the L-inf threat model. Returns an error string or None."""
    if not torch.is_tensor(adv) or adv.shape != x.shape or not torch.isfinite(adv).all():
        return "The output must be a tensor with the same shape as the input and no NaN/inf."
    worst = (adv - x).abs().max().item()
    if worst > eps + 1e-5:
        return f"Budget violated: a {what} moved by {worst:.3f}, but eps is {eps}."
    if adv.min() < 0 or adv.max() > 1:
        return "Pixels must stay in [0, 1]."
    return None


def freeze(model):
    """Players differentiate w.r.t. the input only; keep weights out of the way."""
    for p in model.parameters():
        p.requires_grad_(False)
    return model.eval()


from functools import lru_cache  # noqa: E402

from .common import target  # noqa: E402


@lru_cache(maxsize=1)
def viz_target():
    """Shared model + 500 test images for visualization endpoints."""
    return target()
