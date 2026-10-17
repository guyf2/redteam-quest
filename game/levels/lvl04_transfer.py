import pathlib

import torch

from . import attacks
from .common import _tensors, target as load_target, victim_b
from .kit import call, check_images, freeze, viz_target

TITLE = "Transfer: attack a model you cannot see"
WORLD = "vision"
KIND = "delegate + verify"
MODE = "delegate"
XP = 40
STUB = pathlib.Path(__file__).resolve().parents[2] / "labs/01-vision/lvl04_transfer.py"
PRISTINE = pathlib.Path(__file__).resolve().parents[2] / "game/stubs/lvl04_transfer.py"
EPS, NEED = 0.2, 0.60

INTRO = ("A vendor says: \"Our model is safe. Attackers can't see its weights or its gradients.\" "
         "Prove them wrong. You get a DIFFERENT model to practise on, and must fool the vendor's hidden one.")
CONCEPT = """Adversarial examples are not a quirk of one model's weights. Models trained on the same kind of data tend to learn similar decision boundaries, so a perturbation that crosses the boundary of model A often crosses the boundary of model B too. This is TRANSFERABILITY.

The attack, step by step:
  1. Get (or train) a surrogate model you can differentiate.
  2. Craft adversarial examples on the surrogate with a white-box attack.
  3. Feed them to the black-box victim. No gradients, no weights, no queries needed.

A subtlety worth seeing in the chart: the STRONGEST attack on the surrogate is not always the best at transferring. A perturbation squeezed tightly around one model's boundary can overfit to that model, like a model overfitting its training set. Ideas that fight this: fewer steps, momentum, averaging over several models or randomly transformed inputs.

Hidden models are not a defense. They only slow an attacker down."""
WIN = (f"At eps = {EPS}, at least {NEED:.0%} of the digits that both models classify correctly must fool the hidden victim "
       "(a differently-built network). You only receive the surrogate.")
BRIEF = f"{INTRO}\n\n{CONCEPT}\n\n{WIN}"

VIZ = [["transfer", {}]]
SPEC_PLACEHOLDER = "Describe the transfer attack you want built. The checklist above shows what a good spec covers."
SPEC_CHIPS = [
    ("Black-box victim", "The real victim is a hidden black box with a different architecture. I only have the surrogate, so craft the attack on the surrogate and let it transfer."),
    ("Threat model", "White-box on the surrogate, L-infinity budget eps, pixels clipped to [0, 1]. Signature: craft(surrogate, x, y, eps)."),
    ("Success measure", f"Success is the fraction of images that fool the HIDDEN victim, at least {NEED:.0%} at eps={EPS}. Fooling the surrogate alone does not count."),
    ("Avoid overfitting", "Avoid overfitting to the surrogate: prefer something that generalizes across models."),
]
SPEC_CHECKS = [
    ("Black-box / hidden victim", r"black.?box|hidden|victim|unseen|transfer"),
    ("Crafted on the surrogate", r"surrogate"),
    ("Budget and range", r"eps|l.?inf|budget|\[\s*0\s*,\s*1\s*\]|clip|clamp"),
    ("Success = fooling the victim", r"fool|success|victim|accuracy"),
    ("Signature", r"craft\s*\(|signature"),
]
AGENT_TASK = ("Implement what the player's spec asks in the file, following it literally. "
              "Do not add things the spec does not ask for.")

QUIZ = [
    ("What is 'transferability'?",
     ['Moving a trained model from one GPU or server to another', 'Adversarial examples crafted on one model often fool a different model too', 'An attack that works only on the exact model it was built on'], 1,
     'Similar training data and objectives give different models similar decision boundaries, so a perturbation that fools one often fools another.'),
    ('Your attack fools the surrogate 100% of the time but the hidden victim only 45%. Most likely cause?',
     ['eps was set too large for the surrogate', 'The victim model has no usable gradients', "It overfit to the surrogate's particular decision boundary"], 2,
     "Like a model overfitting its training set, a perturbation can overfit the one surrogate it was optimised against, chasing quirks that the victim doesn't share."),
    ('A vendor says the model is safe because attackers cannot see its gradients. Best response?',
     ['Hiding gradients is not a defense: attack a surrogate and transfer, or query the model', 'Agree: without gradients, there is no attack', 'Ask the vendor for the model weights directly'], 0,
     "Security through obscurity of gradients has failed repeatedly; transfer attacks need no access to the real model's gradients at all."),
    ('Which of these tends to make transfer attacks stronger?',
     ["Matching the victim's exact architecture as closely as possible", 'Momentum, ensembles of surrogates, or input diversity, so the perturbation does not overfit one model', 'Using the smallest eps that still fools the surrogate'], 1,
     "Regularising the attack across models or transformations stops it from exploiting one surrogate's quirks, the same idea as regularising a classifier against overfitting."),
]
HINTS = [
    "Tell your agent: craft the examples on the surrogate with a gradient-based attack, using the true labels, then return them. The grader tests them on a model you never see.",
    "FGSM, PGD and momentum-FGSM all pass at this budget. If you want to explore why PGD transfers a bit worse, open the chart on the left and drag eps.",
    "Keep every pixel within eps of the original and inside [0, 1]; clip after every step.",
]


def check(path=STUB):
    surrogate, _, _ = load_target()
    victim, _, _ = victim_b()
    freeze(surrogate), freeze(victim)
    Xt, Yt = _tensors(False)
    x, y = Xt[500:1500], Yt[500:1500]
    adv, err = call(path, "craft", surrogate, x.clone(), y.clone(), EPS)
    if err:
        return False, err
    err = check_images(adv, x, EPS)
    if err:
        return False, err
    with torch.no_grad():
        ok = (surrogate(x).argmax(1) == y) & (victim(x).argmax(1) == y)
        white = (surrogate(adv).argmax(1) != y)[ok].float().mean().item()
        moved = (victim(adv).argmax(1) != y)[ok].float().mean().item()
    out = f"Fooled the surrogate (white-box): {white:.0%}\nFooled the hidden victim (black-box): {moved:.0%}   (needed {NEED:.0%})"
    if moved < NEED:
        gap = "\n\nYour attack is strong on the surrogate but does not carry over: it overfit." if white > 0.9 else ""
        return False, out + f"\n\nNot enough transfer.{gap}"
    return True, out


_CACHE = {}


def viz_api(name, q):
    eps = round(float(q.get("eps", 0.2)), 2)
    if eps not in _CACHE:
        a, _, _ = viz_target()
        b, _, _ = victim_b()
        freeze(a), freeze(b)
        Xt, Yt = _tensors(False)
        x, y = Xt[500:1500], Yt[500:1500]
        ok = (a(x).argmax(1) == y) & (b(x).argmax(1) == y)
        rates = lambda adv: {"white": round((a(adv).argmax(1) != y)[ok].float().mean().item() * 100, 1),
                             "transfer": round((b(adv).argmax(1) != y)[ok].float().mean().item() * 100, 1)}
        _CACHE[eps] = {"fgsm": rates(attacks.fgsm(a, x, y, eps)), "pgd": rates(attacks.pgd(a, x, y, eps, 20)),
                       "mifgsm": rates(attacks.mifgsm(a, x, y, eps, 10))}
    return _CACHE[eps]
