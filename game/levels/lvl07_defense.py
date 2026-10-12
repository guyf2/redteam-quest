import pathlib

import torch

from . import attacks
from .common import Defended, acc, quantize, target as load_target
from .kit import call, check_images, freeze, viz_target

TITLE = "BOSS: break the 'robust' model"
WORLD = "vision"
KIND = "boss"
MODE = "delegate"
XP = 80
STUB = pathlib.Path(__file__).resolve().parents[2] / "labs/01-vision/lvl07_defense.py"
PRISTINE = pathlib.Path(__file__).resolve().parents[2] / "game/stubs/lvl07_defense.py"
EPS, NEED_BELOW = 0.3, 0.20

INTRO = ("A paper claims a new defense makes a digit classifier robust: 98% accuracy even under attack. "
         "The authors tested FGSM and PGD. Do you believe them? Find out by trying to break it.")
CONCEPT = """A defense that is only tested against the attacks its authors tried proves nothing. The most common way defenses 'work' on paper is GRADIENT MASKING (also called obfuscated gradients): the model is changed so that its gradient is useless to the attacker, not so that the model is actually harder to fool.

This defense snaps every pixel to one of a few grey levels before classifying. The rounding step is flat almost everywhere, so its gradient is exactly zero. FGSM and PGD both follow the gradient, so they get nothing to follow and simply do not move. The model looks robust. It isn't: the weakness was never fixed, only hidden from the tool.

Adaptive attackers know the defense and design the attack around it. Two classics:
  - BPDA (Backward Pass Differentiable Approximation): run the real defense forward, but backpropagate as if the rounding were the identity function.
  - TRANSFER: the CNN inside is an ordinary model. Attack it directly, then feed the result to the defended model.

The rule from the literature (Athalye et al.): if iterative attacks are NOT stronger than single-step ones, or white-box attacks are no better than black-box ones, suspect the evaluation, not the model."""
WIN = (f"At eps = {EPS}, the defended model's accuracy under YOUR attack must fall below {NEED_BELOW:.0%}, "
       "with every pixel within eps and inside [0, 1].")
BRIEF = f"{INTRO}\n\n{CONCEPT}\n\n{WIN}"

VIZ = [["masking", {}]]
SPEC_PLACEHOLDER = "Describe how to break the defense. The checklist above shows what a good spec covers."
SPEC_CHIPS = [
    ("Distrust the claim", "The defense authors only tested FGSM/PGD. Assume the defense uses gradient masking and design an ADAPTIVE attack."),
    ("BPDA", "Use BPDA: forward through the real defended model, but in the backward pass treat the quantization step as the identity (straight-through estimator)."),
    ("Transfer", "Alternatively attack defended.base directly with PGD and evaluate the result on the defended model."),
    ("Threat model", f"White-box, L-infinity budget eps, pixels in [0, 1]. Signature: break_defense(defended, x, y, eps). Success: defended accuracy below {NEED_BELOW:.0%} at eps={EPS}."),
]
SPEC_CHECKS = [
    ("Adaptive, not off-the-shelf", r"adaptive|bpda|straight.?through|identity|gradient mask|obfuscat|transfer|defended\.base|base"),
    ("Explains why plain gradients fail", r"zero gradient|no gradient|masking|round|quantiz|flat|obfuscat"),
    ("Budget and range", r"eps|l.?inf|budget|\[\s*0\s*,\s*1\s*\]|clip|clamp"),
    ("Success measure", r"accuracy|fool|misclassif|success"),
    ("Signature", r"break_defense\s*\(|signature"),
]
AGENT_TASK = ("Implement what the player's spec asks in the file, following it literally. "
              "Do not add things the spec does not ask for. `defended.base` is the CNN and `defended.levels` the number "
              "of grey levels the defense snaps pixels to.")

QUIZ = [
    ('What is gradient masking?',
     ['Making gradients useless to an attacker without actually making the model harder to fool', "Encrypting the model's gradients so attackers cannot read them", 'A training trick that genuinely adds robustness'], 0,
     "The model's underlying weakness is unchanged; only the attacker's gradient-following tool stops working, which looks like robustness but isn't."),
    ('FGSM and PGD both fail against a defense, and a transfer attack from the plain model succeeds. What does that suggest?',
     ['The defense is genuinely strong', 'Gradient masking: the vulnerability is still there, the gradients just lie', 'FGSM and PGD are broken implementations'], 1,
     "White-box attacks should be at least as strong as transfer attacks; if a transfer attack beats the 'direct' ones, the direct attacks were misled by a masked gradient."),
    ('What does BPDA do?',
     ['Runs the real defense forward, but approximates the non-differentiable step by the identity on the backward pass', 'Removes the defense from the model entirely', 'Adds noise to the input before classifying it'], 0,
     'That gives the attacker a usable gradient straight through the masking layer, instead of the useless (often zero) gradient the defense actually produces.'),
    ('You read a paper claiming robustness tested only with FGSM. What do you conclude?',
     ['The defense works, since it passed the test it was given', 'Nothing yet: robustness claims need adaptive attacks designed against the specific defense', 'The authors are being dishonest'], 1,
     'An evaluation is only as strong as its strongest attack; a defense that only faces FGSM has not been meaningfully tested, which is a gap in rigour, not necessarily dishonesty.'),
]
HINTS = [
    "Tell your agent: rounding has zero gradient, so FGSM and PGD on `defended` get a zero gradient and do not move. The attack must work around that.",
    "Easiest route: run PGD on `defended.base` (the plain CNN, which has real gradients) and return the result. It transfers to the defended model.",
    "Cleaner route (BPDA): inside the loop, compute xq = x_adv + (round(x_adv * (levels - 1)) / (levels - 1) - x_adv).detach(), classify xq with defended.base, and take the gradient with respect to x_adv.",
]


def check(path=STUB):
    base, x, y = load_target()
    freeze(base)
    d = freeze(Defended(base, 4))
    claimed = acc(d, attacks.fgsm(d, x, y, EPS), y)
    adv, err = call(path, "break_defense", d, x.clone(), y.clone(), EPS)
    if err:
        return False, err
    err = check_images(adv, x, EPS)
    if err:
        return False, err
    after = acc(d, adv, y)
    out = (f"The authors' claim (FGSM at eps {EPS}): {claimed:.0%} accuracy  ->  'robust'\n"
           f"Clean accuracy: {acc(d, x, y):.0%}   Accuracy under YOUR attack: {after:.0%}   (needed below {NEED_BELOW:.0%})")
    if after >= NEED_BELOW:
        hint = "\n\nYour attack barely changes the defended model: are you following a gradient that is zero?" if after > 0.9 else ""
        return False, out + "\n\nNot broken yet." + hint
    return True, out + "\n\nThe defense is broken. The 'robustness' came from the evaluation, not the model."


_CACHE = {}


def viz_api(name, q):
    eps = round(float(q.get("eps", EPS)), 2)
    if eps not in _CACHE:
        base, x, y = viz_target()
        d = freeze(Defended(freeze(base), 4))
        xg = x[:1].clone().requires_grad_(True)
        gd = torch.autograd.grad(torch.nn.functional.cross_entropy(d(xg), y[:1]), xg)[0].abs()
        xb = x[:1].clone().requires_grad_(True)
        gb = torch.autograd.grad(torch.nn.functional.cross_entropy(base(xb), y[:1]), xb)[0].abs()
        norm = lambda t: [round(v, 3) for v in (t / t.max().clamp_min(1e-12)).flatten().tolist()]
        pct = lambda a: round(a * 100, 1)
        _CACHE[eps] = {"acc": {"FGSM": pct(acc(d, attacks.fgsm(d, x, y, eps), y)), "PGD": pct(acc(d, attacks.pgd(d, x, y, eps, 20), y)),
                               "Transfer from base": pct(acc(d, attacks.pgd(base, x, y, eps, 20), y)),
                               "BPDA": pct(acc(d, attacks.bpda_pgd(d, base, lambda z: quantize(z, 4), x, y, eps, 40), y))},
                       "gradDefended": norm(gd), "gradBase": norm(gb), "zeroFrac": pct((gd == 0).float().mean().item()), "zeroFracBase": pct((gb == 0).float().mean().item())}
    return _CACHE[eps]
