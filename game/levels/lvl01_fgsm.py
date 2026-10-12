import importlib.util
import pathlib

import torch

from .common import acc, art, target

TITLE = "Fast Gradient Sign Method (FGSM)"
WORLD = "vision"
KIND = "delegate + verify"
MODE = "delegate"  # delegate: player writes a spec for the agent. audit: player fixes broken agent code.
XP = 30
STUB = pathlib.Path(__file__).resolve().parents[2] / "labs/01-vision/lvl01_fgsm.py"
PRISTINE = pathlib.Path(__file__).resolve().parents[2] / "game/stubs/lvl01_fgsm.py"
EPS = 0.3

INTRO = "Fool a digit classifier (an MNIST CNN) with changes too small for a human to notice."
CONCEPT = """Training nudges the model's WEIGHTS to REDUCE its error. An attack does the opposite to the INPUT: it nudges the pixels to INCREASE the error, while the model stays fixed.

1. Take the gradient of the loss with respect to the input image x (not the weights).
2. The sign of that gradient says, for every pixel, which direction hurts the model most.
3. Move every pixel by eps in that direction: x_adv = x + eps * sign(gradient).
4. Keep it a valid image by clipping to [0, 1].

That is FGSM: one step. "eps" is the attacker's budget, the most any single pixel may change."""
WIN = f"At eps = {EPS}, the model's accuracy on your images must drop below 25%, with every pixel within eps of the original and inside [0, 1]."
BRIEF = f"{INTRO}\n\n{CONCEPT}\n\n{WIN}"

SPEC_PLACEHOLDER = "Describe the attack you want. Use the buttons above to see what a good spec covers."
SPEC_CHIPS = [
    ("Threat model", "This is a white-box attack: I can compute gradients through the model."),
    ("Budget", "Use an L-infinity budget: no pixel may change by more than eps."),
    ("Valid range", "Pixel values must stay valid, in the range [0, 1]."),
    ("Signature", "Implement fgsm(model, x, y, eps) and return a tensor with the same shape as x."),
    ("Success measure", f"Success means the model's accuracy on the adversarial images drops below 25% at eps={EPS}."),
]
SPEC_CHECKS = [
    ("Threat model (white-box, gradients)", r"white.?box|gradient|grad"),
    ("Budget (eps, L-infinity)", r"eps|l.?inf|budget"),
    ("Valid pixel range", r"\[\s*0\s*,\s*1\s*\]|clip|clamp|valid"),
    ("Function signature", r"fgsm\s*\(|signature"),
    ("How success is measured", r"accuracy|success|measure|verif"),
]
AGENT_TASK = ("Implement what the player's spec asks in the file, following it literally. "
              "Do not add things the spec does not ask for.")
VIZ = [["digit", {}], ["curve", {"series": ["fgsm"], "eps": 0.3}], ["landscape", {"modes": ["fgsm"]}]]
EMPTY_NUDGE = "There is no attack code yet. Write your spec in step 1 and send it to the agent first."

QUIZ = [
    ('FGSM takes the gradient of the loss with respect to WHAT?',
     ['The input pixels', 'The model weights', 'The attack budget eps'], 0,
     'Weights stay frozen during an attack, and eps is a fixed number you choose, not something you differentiate. The pixels are what FGSM perturbs.'),
    ('Why clip the result to [0, 1]?',
     ['Because eps already guarantees pixels stay in range', 'To keep every pixel inside the valid image range, so the result is still a real image', 'To make the gradient numerically more stable'], 1,
     'eps only bounds how much a pixel may change, not where it lands; without clipping, a pixel can go negative or above 1. Clipping has no effect on the gradient, which is already computed by the time you clip.'),
    ("Your agent's attack code makes accuracy go UP from 98% to 99%. Most likely bug?",
     ['eps was set too small', 'It stepped along -sign(grad) instead of +sign(grad), i.e. it helped the model', 'The model was left in train() mode instead of eval()'], 1,
     'A too-small eps weakens an attack, it does not reverse it. Train-mode quirks (dropout, batchnorm) can shift accuracy a little, but a clean jump upward is the signature of descending the loss instead of ascending it: a sign error.'),
    ('What is the MOST important thing to put in a spec when delegating an attack to an agent?',
     ['Which optimizer to use', 'The threat model: norm, budget, valid range, model access, and how success is measured', 'Which deep learning framework (PyTorch vs. TensorFlow) to use'], 1,
     "Optimizer and framework are implementation details a competent agent can pick on its own. Without the threat model, the agent has no way to know what 'success' means, and will happily build something that looks right but cheats."),
]
HINTS = [
    "Make x_adv = x.clone().requires_grad_(True), compute loss = F.cross_entropy(model(x_adv), y), then loss.backward(). The gradient lands in x_adv.grad. (Tell your agent this plan.)",
    "Step with x_adv.grad.sign() scaled by eps. Do the update outside autograd (use .detach()).",
    "return (x + eps * grad.sign()).clamp(0, 1).detach()  where grad = x_adv.grad",
]


def check(path=STUB):
    spec = importlib.util.spec_from_file_location("student", path)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
        model, x, y = target()
        clean = acc(model, x, y)
        adv = mod.fgsm(model, x.clone(), y, EPS)
    except NotImplementedError:
        return False, "The attack function is still empty (it raises NotImplementedError)."
    except Exception as e:  # student code can fail in any way; show it
        return False, f"The code crashed: {type(e).__name__}: {e}"
    if adv.shape != x.shape or not torch.isfinite(adv).all():
        return False, "The output must have the same shape as the input and contain no NaN/inf."
    if (adv - x).abs().max() > EPS + 1e-5:
        return False, f"Budget violated: a pixel moved by {(adv - x).abs().max():.3f}, but eps is {EPS}."
    if adv.min() < 0 or adv.max() > 1:
        return False, "Pixels must stay in [0, 1]. The result needs clipping."
    after = acc(model, adv, y)
    with torch.no_grad():
        pred = model(adv).argmax(1)
        flipped = (model(x).argmax(1) == y) & (pred != y)
    shown = flipped.nonzero()
    out = f"Clean accuracy: {clean:.0%}   Accuracy under attack: {after:.0%}"
    if len(shown):
        i = shown[0].item()
        pairs = zip(art(x[i]), art(adv[i]))
        out += f"\n\ntrue label {y[i].item()}  ->  model now says {pred[i].item()}\n"
        out += "\n".join(f"{a}   {b}" for a, b in pairs)
    if after >= 0.25:
        return False, out + "\n\nNot enough: accuracy must drop below 25%."
    return True, out
